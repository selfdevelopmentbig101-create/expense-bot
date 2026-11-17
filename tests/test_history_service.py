from datetime import datetime, timedelta, timezone

from app.db.seed import seed_default_categories
from app.services.categories import list_categories
from app.services.debts import add_debt_entry, get_or_create_person, undo_debt_entry
from app.services.history import recent_records
from app.services.transactions import save_transaction, undo_transaction
from app.services.users import get_or_create_user

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)


async def setup(session, telegram_id=1):
    await seed_default_categories(session)
    user, _ = await get_or_create_user(session, telegram_id, None)
    food = (await list_categories(session, user.id, "expense"))[0]
    return user, food


async def tx(session, user, food, minutes, amount=1_000):
    return await save_transaction(session, user_id=user.id, category_id=food.id, entry_type="expense",
                                  amount=amount, currency="UZS", note=None,
                                  now=NOW + timedelta(minutes=minutes))


async def test_the_last_ten_records_of_both_kinds_newest_first(session):
    user, food = await setup(session)
    person = await get_or_create_person(session, user.id, "Aziz", NOW)
    for i in range(8):
        await tx(session, user, food, i)
    for i in range(5):
        await add_debt_entry(session, user_id=user.id, person_id=person.id, kind="lent",
                             amount=100 + i, currency="UZS", now=NOW + timedelta(minutes=100 + i))
    items = await recent_records(session, user.id)
    assert len(items) == 10
    assert [i.kind for i in items[:5]] == ["d"] * 5  # the five newest are the debts
    assert [i.created_at for i in items] == sorted((i.created_at for i in items), reverse=True)


async def test_history_is_isolated_between_users(session):
    user, food = await setup(session)
    other, _ = await get_or_create_user(session, 2, None)
    await tx(session, user, food, 0)
    assert await recent_records(session, other.id) == []


async def test_deleting_from_history_shrinks_the_list(session):
    user, food = await setup(session)
    first = await tx(session, user, food, 0)
    second = await tx(session, user, food, 1)
    person = await get_or_create_person(session, user.id, "Aziz", NOW)
    entry = await add_debt_entry(session, user_id=user.id, person_id=person.id, kind="borrowed",
                                 amount=500, currency="UZS", now=NOW + timedelta(minutes=2))
    assert [(i.kind, i.id) for i in await recent_records(session, user.id)] == [
        ("d", entry.id), ("t", second.id), ("t", first.id),
    ]
    assert await undo_transaction(session, user.id, second.id) is not None
    assert await undo_debt_entry(session, user.id, entry.id) is not None
    assert [(i.kind, i.id) for i in await recent_records(session, user.id)] == [("t", first.id)]
    # a second tap on the same button finds nothing
    assert await undo_transaction(session, user.id, second.id) is None
