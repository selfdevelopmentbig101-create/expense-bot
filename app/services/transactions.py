"""Saving, undoing and summing income/expense records."""
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, Transaction


@dataclass(frozen=True, slots=True)
class TransactionView:
    """A record together with its category's display data."""

    id: int
    type: str
    amount: int
    currency: str
    note: str | None
    created_at: datetime
    name_key: str | None
    name: str
    emoji: str


_VIEW_COLUMNS = (
    Transaction.id,
    Transaction.type,
    Transaction.amount,
    Transaction.currency,
    Transaction.note,
    Transaction.created_at,
    Category.name_key,
    Category.name,
    Category.emoji,
)


def _view(row) -> TransactionView:
    return TransactionView(*row)


async def save_transaction(
    session: AsyncSession,
    *,
    user_id: int,
    category_id: int,
    entry_type: str,
    amount: int,
    currency: str,
    note: str | None,
    idempotency_key: str | None = None,
    now: datetime | None = None,
) -> Transaction:
    transaction = Transaction(
        user_id=user_id,
        category_id=category_id,
        type=entry_type,
        amount=amount,
        currency=currency,
        note=note,
        created_at=now or datetime.now(timezone.utc),
        idempotency_key=idempotency_key,
    )
    session.add(transaction)
    await session.flush()
    return transaction


async def get_transaction_view(
    session: AsyncSession, user_id: int, transaction_id: int
) -> TransactionView | None:
    row = (
        await session.execute(
            select(*_VIEW_COLUMNS)
            .join(Category, Category.id == Transaction.category_id)
            .where(Transaction.id == transaction_id, Transaction.user_id == user_id)
        )
    ).first()
    return _view(row) if row else None


async def undo_transaction(
    session: AsyncSession, user_id: int, transaction_id: int
) -> TransactionView | None:
    """Delete one of the user's records. Returns what was deleted, or None if it is gone."""
    view = await get_transaction_view(session, user_id, transaction_id)
    if view is None:
        return None
    result = await session.execute(
        delete(Transaction).where(
            Transaction.id == transaction_id, Transaction.user_id == user_id
        )
    )
    if result.rowcount != 1:  # deleted by someone else a moment ago
        return None
    return view


async def get_last_transaction_id(session: AsyncSession, user_id: int) -> int | None:
    return await session.scalar(
        select(Transaction.id)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .limit(1)
    )


async def totals_between(
    session: AsyncSession,
    user_id: int,
    entry_type: str,
    start: datetime,
    end: datetime,
) -> dict[str, int]:
    """Sum per currency for [start, end). Currencies are never mixed."""
    rows = await session.execute(
        select(Transaction.currency, func.sum(Transaction.amount))
        .where(
            Transaction.user_id == user_id,
            Transaction.type == entry_type,
            Transaction.created_at >= start,
            Transaction.created_at < end,
        )
        .group_by(Transaction.currency)
    )
    return {currency: int(total) for currency, total in rows.all()}


async def list_between(
    session: AsyncSession, user_id: int, start: datetime, end: datetime
) -> list[TransactionView]:
    """Records in [start, end), oldest first."""
    rows = await session.execute(
        select(*_VIEW_COLUMNS)
        .join(Category, Category.id == Transaction.category_id)
        .where(
            Transaction.user_id == user_id,
            Transaction.created_at >= start,
            Transaction.created_at < end,
        )
        .order_by(Transaction.created_at, Transaction.id)
    )
    return [_view(row) for row in rows.all()]


async def get_last_transaction_stamp(
    session: AsyncSession, user_id: int
) -> tuple[int, datetime] | None:
    row = (
        await session.execute(
            select(Transaction.id, Transaction.created_at)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc(), Transaction.id.desc())
            .limit(1)
        )
    ).first()
    return (row[0], row[1]) if row else None


async def recent_transactions(
    session: AsyncSession, user_id: int, limit: int = 10
) -> list[TransactionView]:
    """The newest records, newest first."""
    rows = await session.execute(
        select(*_VIEW_COLUMNS)
        .join(Category, Category.id == Transaction.category_id)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .limit(limit)
    )
    return [_view(row) for row in rows.all()]


async def all_transactions(session: AsyncSession, user_id: int) -> list[TransactionView]:
    """Every record of the user, oldest first (for the CSV export)."""
    rows = await session.execute(
        select(*_VIEW_COLUMNS)
        .join(Category, Category.id == Transaction.category_id)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at, Transaction.id)
    )
    return [_view(row) for row in rows.all()]
