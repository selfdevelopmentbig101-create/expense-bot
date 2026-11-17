"""Setup check: python -m app.doctor

Tells you, step by step, what is missing before the bot can start.
"""
import asyncio
import sys

from pydantic import ValidationError

OK, BAD = "[ OK ]", "[FAIL]"


async def run() -> int:
    failed = False

    def report(ok: bool, text: str) -> None:
        nonlocal failed
        failed = failed or not ok
        print(f"{OK if ok else BAD} {text}")

    from app.config import Settings

    try:
        settings = Settings()
    except ValidationError as exc:
        fields = ", ".join(".".join(str(part) for part in e["loc"]) for e in exc.errors())
        report(False, f"Settings problem ({fields}). Copy .env.example to .env and fill it in.")
        return 1
    report(True, "Settings loaded from .env")
    report(True, "Access: " + (f"limited to {len(settings.allowed_ids)} user(s)" if settings.allowed_ids else "open to everyone (ALLOWED_USER_IDS is empty)"))

    from app.db.health import DatabaseNotReady, ensure_database_ready
    from app.db.session import create_engine

    engine = create_engine(settings.database_url)
    try:
        await ensure_database_ready(engine)
        report(True, "Database is migrated")
    except DatabaseNotReady as exc:
        report(False, str(exc))
    except Exception as exc:  # unreachable server, wrong path, no permission ...
        report(False, f"Cannot open the database: {type(exc).__name__}")
    finally:
        await engine.dispose()

    from aiogram import Bot
    from aiogram.exceptions import TelegramNetworkError, TelegramUnauthorizedError

    bot = Bot(token=settings.bot_token)
    try:
        me = await bot.get_me()
        report(True, f"Telegram accepts the token: @{me.username}")
    except TelegramUnauthorizedError:
        report(False, "Telegram rejected BOT_TOKEN. Copy it again from @BotFather.")
    except TelegramNetworkError:
        report(False, "Cannot reach Telegram. Check the internet connection of this machine.")
    except Exception as exc:
        report(False, f"Telegram check failed: {type(exc).__name__}")
    finally:
        await bot.session.close()

    print("\nAll good. Start the bot with:  python -m app" if not failed else "\nFix the lines marked [FAIL] and run this check again.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
