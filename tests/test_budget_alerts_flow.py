"""The budget warning as the user sees it: right after tapping a category."""
from datetime import datetime, timezone

from app.core.budgets import BudgetAlert
from app.db.seed import seed_default_categories
from app.services.budgets import set_budget
from app.services.categories import list_categories
from app.services.entry_flow import save_chosen_category
from app.services.pending import PendingState, create_pending
from app.services.users import get_or_create_user

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)


async def save(session, user, category, amount, entry_type="expense", currency="UZS"):
    payload = {"amount": amount, "currency": currency, "type": entry_type, "note": None}
    pending = await create_pending(session, user.id, PendingState.CHOOSE_CATEGORY, payload, NOW)
    return await save_chosen_category(session, user, pending.token, category.id, NOW)


async def test_the_saved_entry_carries_the_budget_alert(session):
    await seed_default_categories(session)
    user, _ = await get_or_create_user(session, 1, None)
    expense = await list_categories(session, user.id, "expense")
    income = await list_categories(session, user.id, "income")
    food = expense[0]
    await set_budget(session, user.id, food.id, 300_000, "UZS")

    first = await save(session, user, food, 100_000)
    assert first.budget is None
    second = await save(session, user, food, 150_000)  # 250 000 = 83%
    assert second.budget.alert is BudgetAlert.WARNING and second.budget.percent == 83
    third = await save(session, user, food, 60_000)  # 310 000 = 103%
    assert third.budget.alert is BudgetAlert.EXCEEDED and third.budget.spent == 310_000
    fourth = await save(session, user, food, 1_000)
    assert fourth.budget is None
    other_category = await save(session, user, expense[1], 999_999)
    assert other_category.budget is None
    salary = await save(session, user, income[0], 5_000_000, entry_type="income")
    assert salary.budget is None
