from datetime import datetime, timedelta, timezone

from app.core.budgets import BudgetAlert
from app.db.seed import seed_default_categories
from app.services.budgets import (
    budget_overview,
    check_budget_after_save,
    remove_budget,
    set_budget,
)
from app.services.categories import add_category, list_categories, remove_category
from app.services.transactions import save_transaction
from app.services.users import get_or_create_user
from app.utils.timezone import local_month_bounds

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)
LAST_MONTH = NOW - timedelta(days=30)


async def setup(session, telegram_id=1):
    await seed_default_categories(session)
    user, _ = await get_or_create_user(session, telegram_id, None)
    expense = await list_categories(session, user.id, "expense")
    income = await list_categories(session, user.id, "income")
    await session.commit()
    return user, expense, income


async def spend(session, user, category, amount, currency="UZS", now=NOW, entry_type="expense"):
    """Save an expense and run the budget check, like the bot does."""
    await save_transaction(session, user_id=user.id, category_id=category.id, entry_type=entry_type,
                           amount=amount, currency=currency, note=None, now=now)
    return await check_budget_after_save(session, user, category_id=category.id,
                                         currency=currency, amount=amount, now=now)


async def test_set_change_and_remove_a_budget(session):
    user, expense, _ = await setup(session)
    food = expense[0]
    created = await set_budget(session, user.id, food.id, 300_000, "UZS")
    assert (created.limit_amount, created.currency) == (300_000, "UZS")
    changed = await set_budget(session, user.id, food.id, 400_000, "UZS")
    assert changed.id == created.id and changed.limit_amount == 400_000  # one budget per category
    assert await remove_budget(session, user.id, food.id) is True
    assert await remove_budget(session, user.id, food.id) is False


async def test_only_usable_expense_categories_can_have_a_budget(session):
    user, expense, income = await setup(session)
    other, _ = await get_or_create_user(session, 2, None)
    assert await set_budget(session, user.id, income[0].id, 1_000, "UZS") is None
    assert await set_budget(session, user.id, expense[0].id, 0, "UZS") is None
    assert await set_budget(session, user.id, 99_999, 1_000, "UZS") is None
    _, theirs = await add_category(session, other.id, "expense", "Secret")
    assert await set_budget(session, user.id, theirs.id, 1_000, "UZS") is None
    _, mine = await add_category(session, user.id, "expense", "Pets")
    await spend(session, user, mine, 1)
    await remove_category(session, user.id, mine.id)  # has a record: hidden
    assert await set_budget(session, user.id, mine.id, 1_000, "UZS") is None


async def test_overview_shows_this_months_spending_of_the_budget_currency_only(session):
    user, expense, income = await setup(session)
    food, transport = expense[0], expense[1]
    await set_budget(session, user.id, food.id, 300_000, "UZS")
    await spend(session, user, food, 100_000)
    await spend(session, user, food, 50_000, now=LAST_MONTH)  # last month: not counted
    await spend(session, user, food, 5_000, currency="USD")  # other currency: not counted
    await spend(session, user, transport, 999)  # other category
    start, end = local_month_bounds(NOW, "Asia/Tashkent")
    items = await budget_overview(session, user.id, start, end)
    assert [(i.name, i.limit, i.spent, i.percent) for i in items] == [("Food", 300_000, 100_000, 33)]


async def test_overview_hides_budgets_of_hidden_categories_and_other_users(session):
    user, _, _ = await setup(session)
    other, _ = await get_or_create_user(session, 2, None)
    _, pets = await add_category(session, user.id, "expense", "Pets")
    await set_budget(session, user.id, pets.id, 1_000, "UZS")
    await spend(session, user, pets, 10)
    start, end = local_month_bounds(NOW, "Asia/Tashkent")
    assert len(await budget_overview(session, user.id, start, end)) == 1
    assert await budget_overview(session, other.id, start, end) == []
    await remove_category(session, user.id, pets.id)
    assert await budget_overview(session, user.id, start, end) == []


async def test_warning_at_80_percent_and_at_100_percent(session):
    user, expense, _ = await setup(session)
    food = expense[0]
    await set_budget(session, user.id, food.id, 1_000, "UZS")
    assert await spend(session, user, food, 790) is None  # 79%
    warning = await spend(session, user, food, 10)  # 80%
    assert warning.alert is BudgetAlert.WARNING and (warning.spent, warning.percent) == (800, 80)
    assert await spend(session, user, food, 100) is None  # 90%: the warning was already given
    exceeded = await spend(session, user, food, 100)  # 100%
    assert exceeded.alert is BudgetAlert.EXCEEDED and exceeded.percent == 100
    assert await spend(session, user, food, 50) is None  # already over: no nagging


async def test_one_big_expense_gives_only_the_100_percent_alert(session):
    user, expense, _ = await setup(session)
    await set_budget(session, user.id, expense[0].id, 1_000, "UZS")
    status = await spend(session, user, expense[0], 1_500)
    assert status.alert is BudgetAlert.EXCEEDED and status.percent == 150


async def test_no_alert_without_a_budget_or_for_another_currency_or_last_months_spending(session):
    user, expense, _ = await setup(session)
    food, transport = expense[0], expense[1]
    await set_budget(session, user.id, food.id, 1_000, "UZS")
    assert await spend(session, user, transport, 5_000) is None  # no budget for Transport
    assert await spend(session, user, food, 5_000, currency="USD") is None  # budget is in UZS
    await spend(session, user, food, 900, now=LAST_MONTH)
    assert await spend(session, user, food, 100) is None  # only 10% of THIS month
