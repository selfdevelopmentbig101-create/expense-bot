"""Routes typed text to the flow that asked for it (name, date, amount, time ...)."""
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.handlers.budget_cmd import handle_budget_text
from app.handlers.categories_cmd import handle_category_text
from app.handlers.debt_flow import handle_pending_text
from app.handlers.settings_cmd import handle_settings_text
from app.services.pending import (
    BUDGET_TEXT_STATES,
    CATEGORY_TEXT_STATES,
    SETTINGS_TEXT_STATES,
    Pending,
)


async def route_pending_text(
    message: Message, session: AsyncSession, user: User, pending: Pending
) -> None:
    if pending.state in CATEGORY_TEXT_STATES:
        await handle_category_text(message, session, user, pending)
    elif pending.state in BUDGET_TEXT_STATES:
        await handle_budget_text(message, session, user, pending)
    elif pending.state in SETTINGS_TEXT_STATES:
        await handle_settings_text(message, session, user, pending)
    else:
        await handle_pending_text(message, session, user, pending)
