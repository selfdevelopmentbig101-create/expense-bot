from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import Category
from app.db.seed import seed_default_categories
from app.services.categories import get_category_for_user, list_categories
from app.services.transactions import (
    get_last_transaction_id,
    list_between,
    save_transaction,
    totals_between,
    undo_transaction,
)
from app.services.users import get_or_create_user
from app.utils.timezone import local_day_bounds

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)


async def setup(session):
    await seed_default_categories(session)
    user, _ = await get_or_create_user(session, 1, None)
    expense = await list_categories(session, user.id, "expense")
    income = await list_categories(session, user.id, "income")
    await session.commit()
    return user, expense, income


async def add(session, user, category, amount=10000, currency="UZS", entry_type="expense",
              note=None, now=NOW, key=None):
    return await save_transaction(
        session, user_id=user.id, category_id=category.id, entry_type=entry_type,
        amount=amount, currency=currency, note=note, idempotency_key=key, now=now,
    )


async def test_expense_and_income_categories_come_from_the_database(session):
    _, expense, income = await setup(session)
    assert [c.name for c in expense] == [
        "Food", "Transport", "Home", "Health", "Clothes", "Fun", "Phone/Internet", "Other",
    ]
    assert [c.name for c in income] == ["Salary", "Gift", "Other income"]


async def test_custom_and_archived_categories(session):
    user, expense, _ = await setup(session)
    other, _ = await get_or_create_user(session, 2, None)
    mine = Category(user_id=user.id, name="Pets", emoji="x", type="expense", sort_order=100)
    theirs = Category(user_id=other.id, name="Secret", emoji="x", type="expense", sort_order=100)
    session.add_all([mine, theirs])
    await session.flush()

    names = [c.name for c in await list_categories(session, user.id, "expense")]
    assert "Pets" in names and "Secret" not in names
    assert await get_category_for_user(session, user.id, theirs.id) is None

    mine.is_archived = True
    await session.flush()
    assert "Pets" not in [c.name for c in await list_categories(session, user.id, "expense")]
    assert await get_category_for_user(session, user.id, mine.id) is None


async def test_save_stores_the_record(session):
    user, expense, _ = await setup(session)
    tx = await add(session, user, expense[0], 10000, note="bread")
    assert tx.id is not None
    assert (tx.amount, tx.currency, tx.type, tx.note) == (10000, "UZS", "expense", "bread")
    assert tx.created_at == NOW


async def test_undo_deletes_and_totals_drop(session):
    user, expense, _ = await setup(session)
    start, end = local_day_bounds(NOW, user.timezone)
    tx = await add(session, user, expense[0], 10000)
    assert await totals_between(session, user.id, "expense", start, end) == {"UZS": 10000}

    view = await undo_transaction(session, user.id, tx.id)
    assert view is not None
    assert (view.amount, view.name, view.type) == (10000, "Food", "expense")
    assert await totals_between(session, user.id, "expense", start, end) == {}


async def test_undo_twice_returns_none(session):
    user, expense, _ = await setup(session)
    tx = await add(session, user, expense[0])
    assert await undo_transaction(session, user.id, tx.id) is not None
    assert await undo_transaction(session, user.id, tx.id) is None


async def test_undo_cannot_touch_another_users_record(session):
    user, expense, _ = await setup(session)
    other, _ = await get_or_create_user(session, 2, None)
    tx = await add(session, user, expense[0])
    assert await undo_transaction(session, other.id, tx.id) is None
    assert await get_last_transaction_id(session, user.id) == tx.id  # still there


async def test_last_transaction_is_the_newest(session):
    user, expense, _ = await setup(session)
    assert await get_last_transaction_id(session, user.id) is None
    await add(session, user, expense[0], now=NOW)
    newest = await add(session, user, expense[1], now=NOW + timedelta(minutes=1))
    await add(session, user, expense[2], now=NOW - timedelta(hours=1))
    assert await get_last_transaction_id(session, user.id) == newest.id


async def test_totals_are_per_type_and_currency_and_day(session):
    user, expense, income = await setup(session)
    start, end = local_day_bounds(NOW, user.timezone)
    await add(session, user, expense[0], 10000)
    await add(session, user, expense[1], 35000)
    await add(session, user, expense[0], 5000, currency="USD")
    await add(session, user, income[0], 2000000, entry_type="income")
    await add(session, user, expense[0], 99999, now=start - timedelta(seconds=1))  # yesterday
    await add(session, user, expense[0], 77777, now=end)  # tomorrow: end is exclusive

    assert await totals_between(session, user.id, "expense", start, end) == {"UZS": 45000, "USD": 5000}
    assert await totals_between(session, user.id, "income", start, end) == {"UZS": 2000000}


async def test_totals_are_isolated_between_users(session):
    user, expense, _ = await setup(session)
    other, _ = await get_or_create_user(session, 2, None)
    start, end = local_day_bounds(NOW, user.timezone)
    await add(session, user, expense[0], 10000)
    assert await totals_between(session, other.id, "expense", start, end) == {}
    assert await list_between(session, other.id, start, end) == []


async def test_list_between_is_oldest_first_with_category_data(session):
    user, expense, income = await setup(session)
    start, end = local_day_bounds(NOW, user.timezone)
    await add(session, user, income[0], 100, entry_type="income", now=NOW + timedelta(minutes=2))
    await add(session, user, expense[0], 50, note="a", now=NOW)
    rows = await list_between(session, user.id, start, end)
    assert [(r.name, r.amount, r.type) for r in rows] == [("Food", 50, "expense"), ("Salary", 100, "income")]
    assert rows[0].note == "a" and rows[0].name_key == "cat.food"


async def test_the_same_idempotency_key_cannot_be_saved_twice(session):
    user, expense, _ = await setup(session)
    await add(session, user, expense[0], key="pending:abc")
    with pytest.raises(IntegrityError):
        await add(session, user, expense[0], key="pending:abc")
