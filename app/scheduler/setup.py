"""The scheduler: when each reminder job runs."""
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.scheduler.jobs import debt_reminders_job, evening_reminders_job
from app.utils.timezone import DEFAULT_TIMEZONE

DEBT_REMINDER_HOUR = 9  # 09:00 Asia/Tashkent


def create_scheduler(
    bot: Bot, session_factory: async_sessionmaker[AsyncSession]
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=DEFAULT_TIMEZONE)
    scheduler.add_job(
        debt_reminders_job,
        CronTrigger(hour=DEBT_REMINDER_HOUR, minute=0, timezone=DEFAULT_TIMEZONE),
        args=[bot, session_factory],
        id="debt_reminders",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,  # still runs if the bot was down at 09:00 but is back within an hour
        replace_existing=True,
    )
    scheduler.add_job(
        evening_reminders_job,
        IntervalTrigger(minutes=1),
        args=[bot, session_factory],
        id="evening_reminders",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
        replace_existing=True,
    )
    return scheduler
