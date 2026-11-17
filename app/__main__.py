"""Entry point: python -m app"""
import asyncio
import contextlib
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramUnauthorizedError
from aiogram.types import BotCommand
from pydantic import ValidationError

from app.config import get_settings
from app.db.health import DatabaseNotReady, ensure_database_ready
from app.db.seed import seed_default_categories
from app.db.session import create_engine, create_session_factory
from app.handlers import (
    budget_cmd,
    categories_cmd,
    debt_flow,
    debts_cmd,
    errors,
    expense_flow,
    export_cmd,
    fallback,
    history,
    reminders_cmd,
    reports_cmd,
    settings_cmd,
    start,
    today,
    undo,
)
from app.healthcheck import heartbeat_loop
from app.i18n import LANGUAGES, t
from app.logging_setup import setup_logging
from app.menu import MENU_COMMANDS
from app.middlewares.access import AccessMiddleware
from app.middlewares.db import DbSessionMiddleware
from app.middlewares.throttle import ThrottleMiddleware
from app.middlewares.user import UserMiddleware
from app.scheduler.setup import create_scheduler
from app.services.pending import purge_expired

logger = logging.getLogger(__name__)



def build_menu(lang: str) -> list[BotCommand]:
    return [BotCommand(command=name, description=t(lang, f"menu.{name}")) for name in MENU_COMMANDS]


async def set_menus(bot: Bot) -> None:
    """The command menu in English by default, and in the user's own language."""
    await bot.set_my_commands(build_menu("en"))
    for lang in LANGUAGES:
        await bot.set_my_commands(build_menu(lang), language_code=lang)


async def main() -> int:
    try:
        settings = get_settings()
    except ValidationError as exc:
        problems = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
        print(f"Configuration problem: {problems}\nCopy .env.example to .env and fill it in.", file=sys.stderr)
        return 2
    setup_logging(settings.log_level)

    engine = create_engine(settings.database_url)
    try:
        await ensure_database_ready(engine)
    except DatabaseNotReady as exc:
        logger.error("%s", exc)
        await engine.dispose()
        return 3
    session_factory = create_session_factory(engine)

    async with session_factory() as session:
        added = await seed_default_categories(session)
        purged = await purge_expired(session)
        await session.commit()
    logger.info("Default categories ready (%d added), %d expired pending removed", added, purged)

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Order matters: flood protection -> access check -> DB session -> user row.
    dp.update.outer_middleware(ThrottleMiddleware())
    dp.update.outer_middleware(AccessMiddleware(settings.allowed_ids))
    dp.update.outer_middleware(DbSessionMiddleware(session_factory))
    dp.update.outer_middleware(UserMiddleware())

    # Order matters: the safety net first, specific commands next, the catch-alls last.
    dp.include_router(errors.router)
    dp.include_router(start.router)
    dp.include_router(today.router)
    dp.include_router(undo.router)
    dp.include_router(reports_cmd.router)
    dp.include_router(budget_cmd.router)
    dp.include_router(settings_cmd.router)
    dp.include_router(export_cmd.router)
    dp.include_router(reminders_cmd.router)
    dp.include_router(history.router)
    dp.include_router(categories_cmd.router)
    dp.include_router(debts_cmd.router)
    dp.include_router(debt_flow.router)
    dp.include_router(expense_flow.router)
    dp.include_router(fallback.router)

    scheduler = create_scheduler(bot, session_factory)
    heartbeat = asyncio.create_task(heartbeat_loop())
    try:
        try:
            me = await bot.get_me()
        except TelegramUnauthorizedError:
            logger.error("Telegram rejected BOT_TOKEN. Copy it again from @BotFather into .env.")
            return 1
        logger.info("Starting @%s (long polling)", me.username)
        try:
            await set_menus(bot)
        except TelegramAPIError:
            logger.warning("Could not set the command menu", exc_info=True)
        scheduler.start()
        logger.info("Reminder scheduler started")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        heartbeat.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat
        if scheduler.running:
            scheduler.shutdown(wait=False)
        await bot.session.close()
        await engine.dispose()
    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(asyncio.run(main()))
