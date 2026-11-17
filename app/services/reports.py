"""Totals per category for a period (the data behind /week and /month)."""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, Transaction


@dataclass(frozen=True, slots=True)
class CategoryTotal:
    type: str  # expense | income
    currency: str
    name_key: str | None
    name: str
    emoji: str
    total: int  # minor units


async def category_totals(
    session: AsyncSession, user_id: int, start: datetime, end: datetime
) -> list[CategoryTotal]:
    """Sum per (type, currency, category) for [start, end). Debts are not here."""
    rows = await session.execute(
        select(
            Transaction.type,
            Transaction.currency,
            Category.name_key,
            Category.name,
            Category.emoji,
            func.sum(Transaction.amount),
        )
        .join(Category, Category.id == Transaction.category_id)
        .where(
            Transaction.user_id == user_id,
            Transaction.created_at >= start,
            Transaction.created_at < end,
        )
        .group_by(
            Transaction.type,
            Transaction.currency,
            Category.id,
            Category.name_key,
            Category.name,
            Category.emoji,
        )
    )
    return [CategoryTotal(*row[:5], int(row[5])) for row in rows.all()]
