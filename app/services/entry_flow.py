"""Business logic of the two-step flow: the user tapped a category."""
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.services.budgets import BudgetStatus, check_budget_after_save
from app.services.categories import get_category_for_user
from app.services.pending import PendingState, consume_pending, get_pending
from app.services.transactions import save_transaction, totals_between
from app.utils.timezone import local_day_bounds


@dataclass(frozen=True, slots=True)
class SavedEntry:
    transaction_id: int
    type: str
    amount: int
    currency: str
    note: str | None
    category_name_key: str | None
    category_name: str
    category_emoji: str
    total_today: int  # same type and currency, including this record
    budget: BudgetStatus | None = None  # set when this expense crossed 80% / 100%


async def save_chosen_category(
    session: AsyncSession,
    user: User,
    token: str,
    category_id: int,
    now: datetime | None = None,
) -> SavedEntry | None:
    """Save the pending amount under the chosen category.

    Returns None when nothing was saved: the pending action is missing, expired,
    replaced, already used (double tap), or the category is not allowed.
    """
    now = now or datetime.now(timezone.utc)

    pending = await get_pending(session, user.id, token, now)
    if pending is None or pending.state != PendingState.CHOOSE_CATEGORY:
        return None
    payload = pending.payload

    category = await get_category_for_user(session, user.id, category_id)
    if category is None or category.type != payload["type"]:
        return None

    # Only one concurrent tap can get past this line.
    if await consume_pending(session, user.id, token, now) is None:
        return None

    transaction = await save_transaction(
        session,
        user_id=user.id,
        category_id=category.id,
        entry_type=payload["type"],
        amount=payload["amount"],
        currency=payload["currency"],
        note=payload.get("note"),
        idempotency_key=f"pending:{token}",  # second safety net against duplicates
        now=now,
    )

    start, end = local_day_bounds(now, user.timezone)
    totals = await totals_between(session, user.id, payload["type"], start, end)
    budget = None
    if payload["type"] == "expense":
        budget = await check_budget_after_save(
            session,
            user,
            category_id=category.id,
            currency=payload["currency"],
            amount=payload["amount"],
            now=now,
        )
    return SavedEntry(
        transaction_id=transaction.id,
        type=payload["type"],
        amount=payload["amount"],
        currency=payload["currency"],
        note=payload.get("note"),
        category_name_key=category.name_key,
        category_name=category.name,
        category_emoji=category.emoji,
        total_today=totals.get(payload["currency"], 0),
        budget=budget,
    )
