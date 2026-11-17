"""Sending reminders. The same functions serve the scheduler and the /remindtest command."""
import asyncio
import logging
from datetime import date, datetime

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.reminders import ReminderKind
from app.keyboards.reminder import overdue_keyboard
from app.services.reminder_formatting import render_debt_reminder, render_evening
from app.services.reminders import (
    collect_debt_reminders,
    collect_evening_reminders,
    mark_evening_sent,
    mark_reminded,
)

logger = logging.getLogger(__name__)

PAUSE_BETWEEN_MESSAGES = 0.05  # stay far below Telegram's 30 messages per second


async def send_message(
    bot: Bot, chat_id: int, text: str, markup: InlineKeyboardMarkup | None = None
) -> bool:
    """Send one message. Never raises: a blocked user must not stop the other reminders."""
    for attempt in (1, 2):
        try:
            await bot.send_message(chat_id, text, reply_markup=markup)
            await asyncio.sleep(PAUSE_BETWEEN_MESSAGES)
            return True
        except TelegramRetryAfter as exc:
            if attempt == 2:
                return False
            await asyncio.sleep(exc.retry_after)
        except TelegramForbiddenError:
            logger.info("User %s blocked the bot, reminder skipped", chat_id)
            return False
        except TelegramAPIError:
            logger.warning("Could not send a reminder to %s", chat_id, exc_info=True)
            return False
    return False


async def deliver_debt_reminders(
    bot: Bot,
    session: AsyncSession,
    now: datetime | None = None,
    *,
    user_id: int | None = None,
    only_enabled: bool = True,
    ignore_history: bool = False,
    today_override: date | None = None,
    mark: bool = True,
) -> int:
    """Send every debt reminder that is due. Returns how many were sent.

    mark=True remembers that the debt was reminded today (and commits after each message,
    so a crash never causes duplicates). Manual tests use mark=False.
    """
    reminders = await collect_debt_reminders(
        session,
        now,
        user_id=user_id,
        only_enabled=only_enabled,
        ignore_history=ignore_history,
        today_override=today_override,
    )
    sent = 0
    for reminder in reminders:
        text = render_debt_reminder(reminder.language, reminder)
        markup = None
        if reminder.kind is ReminderKind.OVERDUE:
            markup = overdue_keyboard(reminder.person_id, reminder.currency, reminder.language)
        if await send_message(bot, reminder.telegram_id, text, markup):
            sent += 1
            if mark:
                await mark_reminded(session, reminder.entry_id, reminder.today)
                await session.commit()
    return sent


async def deliver_evening_reminders(
    bot: Bot,
    session: AsyncSession,
    now: datetime | None = None,
    *,
    user_id: int | None = None,
    force: bool = False,
    mark: bool = True,
) -> int:
    reminders = await collect_evening_reminders(session, now, user_id=user_id, force=force)
    sent = 0
    for reminder in reminders:
        if await send_message(bot, reminder.telegram_id, render_evening(reminder.language, reminder)):
            sent += 1
            if mark:
                await mark_evening_sent(session, reminder.user_id, reminder.local_date)
                await session.commit()
    return sent


async def debt_reminders_job(bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Daily at 09:00 (Asia/Tashkent)."""
    try:
        async with session_factory() as session:
            sent = await deliver_debt_reminders(bot, session)
        logger.info("Debt reminders sent: %d", sent)
    except Exception:
        logger.exception("Debt reminder job failed")


async def evening_reminders_job(bot: Bot, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Every minute: sends the evening reminder to whoever chose this time."""
    try:
        async with session_factory() as session:
            sent = await deliver_evening_reminders(bot, session)
        if sent:
            logger.info("Evening reminders sent: %d", sent)
    except Exception:
        logger.exception("Evening reminder job failed")
