"""/week and /month."""
from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.services.report_formatting import render_report
from app.services.reports import category_totals
from app.utils.timezone import local_month_bounds, local_week_bounds

router = Router(name="reports")


async def _send_report(message: Message, session: AsyncSession, user: User, period: str) -> None:
    now = datetime.now(timezone.utc)
    bounds = local_week_bounds if period == "week" else local_month_bounds
    start, end = bounds(now, user.timezone)
    rows = await category_totals(session, user.id, start, end)
    await message.answer(render_report(user.language, user.timezone, period, start, end, rows))


@router.message(Command("week"))
async def cmd_week(message: Message, session: AsyncSession, user: User) -> None:
    await _send_report(message, session, user, "week")


@router.message(Command("month"))
async def cmd_month(message: Message, session: AsyncSession, user: User) -> None:
    await _send_report(message, session, user, "month")
