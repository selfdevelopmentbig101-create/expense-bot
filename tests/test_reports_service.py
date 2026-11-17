from datetime import datetime, timedelta, timezone

from app.db.seed import seed_default_categories
from app.services.categories import list_categories, remove_category
from app.services.debts import add_debt_entry, get_or_create_person
from app.services.reports import category_totals
from app.services.transactions import save_transaction, totals_between, undo_transaction
from app.services.users import get_or_create_user
from app.utils.timezone import local_month_bounds, local_week_bounds

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)  # Tuesday
TZ = "Asia/Tashkent"


async def setup(session, telegram_id=1):
    await seed_default_categories(session)
    user, _ = await get_or_create_user(session, telegram_id, None)
    expense = await list_categories(session, user.id, "expense")
    income = await list_categories(session, user.id, "income")
    await session.commit()
    return user, expense, income


async def add(session, user, category, amount, entry_type="expense", currency="UZS", now=NOW):
    return await save_transaction(
        session, user_id=user.id, category_id=category.id, entry_type=entry_type,
        amount=amount, currency=currency, note=None, now=now,
    )


def as_dict(rows):
    return {(r.type, r.currency, r.name): r.total for r in rows}


async def test_totals_per_category_type_and_currency(session):
    user, expense, income = await setup(session)
    await add(session, user, expense[0], 10_000)
    await add(session, user, expense[0], 5_000)
    await add(session, user, expense[1], 35_000)
    await add(session, user, expense[0], 700, currency="USD")
    await add(session, user, income[0], 2_000_000, entry_type="income")
    start, end = local_week_bounds(NOW, TZ)
    assert as_dict(await category_totals(session, user.id, start, end)) == {
        ("expense", "UZS", "Food"): 15_000,
        ("expense", "UZS", "Transport"): 35_000,
        ("expense", "USD", "Food"): 700,
        ("income", "UZS", "Salary"): 2_000_000,
    }


async def test_week_and_month_cover_different_ranges(session):
    user, expense, _ = await setup(session)
    await add(session, user, expense[0], 1_000, now=NOW)  # this week
    await add(session, user, expense[0], 2_000, now=NOW - timedelta(days=9))  # 8 Nov: this month only
    await add(session, user, expense[0], 4_000, now=NOW - timedelta(days=30))  # October
    week = await category_totals(session, user.id, *local_week_bounds(NOW, TZ))
    month = await category_totals(session, user.id, *local_month_bounds(NOW, TZ))
    assert sum(r.total for r in week) == 1_000
    assert sum(r.total for r in month) == 3_000


async def test_the_week_edge_is_local_midnight(session):
    user, expense, _ = await setup(session)
    start, end = local_week_bounds(NOW, TZ)
    await add(session, user, expense[0], 1, now=start)  # Monday 00:00 local: in
    await add(session, user, expense[0], 10, now=start - timedelta(seconds=1))  # Sunday 23:59:59: out
    await add(session, user, expense[0], 100, now=end - timedelta(seconds=1))  # Sunday 23:59:59: in
    await add(session, user, expense[0], 1000, now=end)  # next Monday: out
    rows = await category_totals(session, user.id, start, end)
    assert sum(r.total for r in rows) == 101


async def test_debts_are_not_in_the_reports(session):
    user, expense, _ = await setup(session)
    await add(session, user, expense[0], 1_000)
    person = await get_or_create_person(session, user.id, "Aziz", NOW)
    await add_debt_entry(session, user_id=user.id, person_id=person.id, kind="borrowed",
                         amount=500_000, currency="UZS", now=NOW)
    rows = await category_totals(session, user.id, *local_week_bounds(NOW, TZ))
    assert sum(r.total for r in rows) == 1_000


async def test_reports_are_isolated_between_users(session):
    user, expense, _ = await setup(session)
    other, _ = await get_or_create_user(session, 2, None)
    await add(session, user, expense[0], 1_000)
    assert await category_totals(session, other.id, *local_week_bounds(NOW, TZ)) == []


async def test_deleting_a_record_updates_the_report(session):
    user, expense, _ = await setup(session)
    keep = await add(session, user, expense[0], 10_000)
    drop = await add(session, user, expense[1], 35_000)
    bounds = local_week_bounds(NOW, TZ)
    assert sum(r.total for r in await category_totals(session, user.id, *bounds)) == 45_000

    await undo_transaction(session, user.id, drop.id)
    rows = await category_totals(session, user.id, *bounds)
    assert as_dict(rows) == {("expense", "UZS", "Food"): 10_000}
    assert await totals_between(session, user.id, "expense", *local_week_bounds(NOW, TZ)) == {"UZS": 10_000}
    assert keep.id is not None


async def test_a_hidden_category_still_counts_in_reports(session):
    from app.services.categories import add_category

    user, _, _ = await setup(session)
    _, pets = await add_category(session, user.id, "expense", "\U0001F436 Pets")
    await add(session, user, pets, 7_000)
    await remove_category(session, user.id, pets.id)  # has records -> hidden
    rows = await category_totals(session, user.id, *local_week_bounds(NOW, TZ))
    assert as_dict(rows) == {("expense", "UZS", "Pets"): 7_000}
