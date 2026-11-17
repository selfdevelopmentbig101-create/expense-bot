"""/today: today's records and totals."""
from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.services.formatting import render_today
from app.services.transactions import list_between
from app.utils.timezone import local_day_bounds

router = Router(name="today")


@router.message(Command("today"))
async def cmd_today(message: Message, session: AsyncSession, user: User) -> None:
    now = datetime.now(timezone.utc)
    start, end = local_day_bounds(now, user.timezone)
    rows = await list_between(session, user.id, start, end)
    await message.answer(render_today(user.language, user.timezone, now, rows))
