"""Monthly budgets per expense category."""
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.budgets import BudgetAlert, crossing_alert, percent_used
from app.db.models import Budget, Category, Transaction, User
from app.services.categories import get_category_for_user
from app.utils.timezone import local_month_bounds


@dataclass(frozen=True, slots=True)
class BudgetProgress:
    category_id: int
    name_key: str | None
    name: str
    emoji: str
    limit: int
    currency: str
    spent: int

    @property
    def percent(self) -> int:
        return percent_used(self.spent, self.limit)


@dataclass(frozen=True, slots=True)
class BudgetStatus:
    """What the user must be told after saving an expense."""

    alert: BudgetAlert
    spent: int
    limit: int
    percent: int
    currency: str


async def set_budget(
    session: AsyncSession, user_id: int, category_id: int, limit: int, currency: str
) -> Budget | None:
    """Create or change a limit. None if the category cannot have a budget."""
    category = await get_category_for_user(session, user_id, category_id)
    if category is None or category.type != "expense" or limit <= 0:
        return None
    budget = await session.scalar(
        select(Budget).where(Budget.user_id == user_id, Budget.category_id == category_id)
    )
    if budget is None:
        budget = Budget(user_id=user_id, category_id=category_id, limit_amount=limit, currency=currency)
        session.add(budget)
    else:
        budget.limit_amount, budget.currency = limit, currency
    await session.flush()
    return budget


async def remove_budget(session: AsyncSession, user_id: int, category_id: int) -> bool:
    result = await session.execute(
        delete(Budget).where(Budget.user_id == user_id, Budget.category_id == category_id)
    )
    return result.rowcount == 1


async def category_spent(
    session: AsyncSession,
    user_id: int,
    category_id: int,
    currency: str,
    start: datetime,
    end: datetime,
) -> int:
    return int(
        await session.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.user_id == user_id,
                Transaction.category_id == category_id,
                Transaction.type == "expense",
                Transaction.currency == currency,
                Transaction.created_at >= start,
                Transaction.created_at < end,
            )
        )
        or 0
    )


async def budget_overview(
    session: AsyncSession, user_id: int, start: datetime, end: datetime
) -> list[BudgetProgress]:
    """All budgets with this month's spending. Hidden categories are left out."""
    rows = await session.execute(
        select(
            Budget.category_id,
            Category.name_key,
            Category.name,
            Category.emoji,
            Budget.limit_amount,
            Budget.currency,
        )
        .join(Category, Category.id == Budget.category_id)
        .where(Budget.user_id == user_id, Category.is_archived.is_(False))
        .order_by(Category.sort_order, Category.id)
    )
    budgets = rows.all()
    if not budgets:
        return []
    spent_rows = await session.execute(
        select(Transaction.category_id, Transaction.currency, func.sum(Transaction.amount))
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.created_at >= start,
            Transaction.created_at < end,
        )
        .group_by(Transaction.category_id, Transaction.currency)
    )
    spent = {(cid, cur): int(total) for cid, cur, total in spent_rows.all()}
    return [BudgetProgress(*row, spent.get((row[0], row[5]), 0)) for row in budgets]


async def check_budget_after_save(
    session: AsyncSession,
    user: User,
    *,
    category_id: int,
    currency: str,
    amount: int,
    now: datetime | None = None,
) -> BudgetStatus | None:
    """Call right AFTER an expense was saved. Returns a status only when it crossed 80% or 100%."""
    budget = await session.scalar(
        select(Budget).where(
            Budget.user_id == user.id,
            Budget.category_id == category_id,
            Budget.currency == currency,  # budgets and spending are never mixed across currencies
        )
    )
    if budget is None:
        return None
    start, end = local_month_bounds(now or datetime.now(timezone.utc), user.timezone)
    after = await category_spent(session, user.id, category_id, currency, start, end)
    alert = crossing_alert(after - amount, after, budget.limit_amount)
    if alert is None:
        return None
    return BudgetStatus(alert, after, budget.limit_amount, percent_used(after, budget.limit_amount), currency)
