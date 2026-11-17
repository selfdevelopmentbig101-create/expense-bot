from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select

from app.db.models import DebtEntry, Person
from app.services.debts import (
    add_debt_entry,
    clean_name,
    close_debt,
    delete_person,
    effective_due_date,
    entries_for_person,
    find_person_by_name,
    get_last_debt_stamp,
    get_or_create_person,
    get_overview,
    get_person,
    get_person_balances,
    normalize_name,
    recent_persons,
    set_due_date,
    undo_debt_entry,
)
from app.services.users import get_or_create_user

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)


def at(hours):
    return NOW + timedelta(hours=hours)


async def make_user(session, telegram_id=1):
    user, _ = await get_or_create_user(session, telegram_id, None)
    return user


async def entry(session, user, person, kind, amount, currency="UZS", hours=0, due=None, note=None):
    return await add_debt_entry(
        session, user_id=user.id, person_id=person.id, kind=kind, amount=amount,
        currency=currency, note=note, due_date=due, now=at(hours),
    )


def test_name_cleaning_and_matching_key():
    assert clean_name("  Aziz   Karimov ") == "Aziz Karimov"
    assert normalize_name("  AZIZ   karimov ") == normalize_name("aziz karimov")
    assert clean_name("x" * 300) == "x" * 100


async def test_people_are_matched_case_insensitively_and_trimmed(session):
    user = await make_user(session)
    first = await get_or_create_person(session, user.id, "Aziz", NOW)
    for variant in (" aziz ", "AZIZ", "aZiZ"):
        assert (await get_or_create_person(session, user.id, variant, NOW)).id == first.id
    assert first.name == "Aziz"  # the first spelling is kept
    assert (await find_person_by_name(session, user.id, "  azIZ")).id == first.id


async def test_people_are_isolated_between_users(session):
    a, b = await make_user(session, 1), await make_user(session, 2)
    pa = await get_or_create_person(session, a.id, "Aziz", NOW)
    pb = await get_or_create_person(session, b.id, "Aziz", NOW)
    assert pa.id != pb.id
    assert await get_person(session, b.id, pa.id) is None
    assert (await find_person_by_name(session, b.id, "aziz")).id == pb.id  # same name, own row
    assert (await find_person_by_name(session, a.id, "aziz")).id == pa.id


async def test_recent_people_are_the_six_latest(session):
    user = await make_user(session)
    people = []
    for i in range(8):
        person = await get_or_create_person(session, user.id, f"P{i}", at(i))
        await entry(session, user, person, "lent", 100, hours=i)
        people.append(person)
    names = [p.name for p in await recent_persons(session, user.id, limit=6)]
    assert names == ["P7", "P6", "P5", "P4", "P3", "P2"]


async def test_recent_people_use_the_last_entry_not_the_creation_time(session):
    user = await make_user(session)
    old = await get_or_create_person(session, user.id, "Old", at(0))
    new = await get_or_create_person(session, user.id, "New", at(1))
    await entry(session, user, old, "lent", 100, hours=0)
    await entry(session, user, new, "lent", 100, hours=1)
    await entry(session, user, old, "lent", 100, hours=5)  # Old was used again
    assert [p.name for p in await recent_persons(session, user.id)] == ["Old", "New"]


async def test_balances_per_currency_and_closed_debts_are_hidden(session):
    user = await make_user(session)
    aziz = await get_or_create_person(session, user.id, "Aziz", NOW)
    bobur = await get_or_create_person(session, user.id, "Bobur", NOW)
    await entry(session, user, aziz, "borrowed", 500_000)
    await entry(session, user, aziz, "lent", 1_000, currency="USD")
    await entry(session, user, bobur, "lent", 200_000)
    await entry(session, user, bobur, "repaid_to_me", 200_000)  # closed

    assert await get_person_balances(session, user.id, aziz.id) == {"UZS": -500_000, "USD": 1_000}
    assert await get_person_balances(session, user.id, bobur.id) == {"UZS": 0}
    overview = await get_overview(session, user.id)
    assert [(p.name, p.balances) for p in overview] == [("Aziz", {"UZS": -500_000, "USD": 1_000})]


async def test_overview_is_isolated_between_users(session):
    a, b = await make_user(session, 1), await make_user(session, 2)
    pa = await get_or_create_person(session, a.id, "Aziz", NOW)
    await entry(session, a, pa, "lent", 100)
    assert await get_overview(session, b.id) == []


async def test_history_is_newest_first_and_limited(session):
    user = await make_user(session)
    person = await get_or_create_person(session, user.id, "Aziz", NOW)
    for i in range(12):
        await entry(session, user, person, "lent", 100 + i, hours=i)
    rows = await entries_for_person(session, user.id, person.id, limit=10)
    assert len(rows) == 10 and rows[0].amount == 111 and rows[0].person_name == "Aziz"


async def test_undo_deletes_the_entry_and_an_orphan_person(session):
    user = await make_user(session)
    person = await get_or_create_person(session, user.id, "Aziz", NOW)
    only = await entry(session, user, person, "borrowed", 500_000)
    view = await undo_debt_entry(session, user.id, only.id)
    assert view is not None and view.amount == 500_000
    assert await get_person(session, user.id, person.id) is None  # no entries left


async def test_undo_keeps_a_person_who_has_other_entries(session):
    user = await make_user(session)
    person = await get_or_create_person(session, user.id, "Aziz", NOW)
    await entry(session, user, person, "borrowed", 500_000, hours=0)
    second = await entry(session, user, person, "repaid_by_me", 100_000, hours=1)
    await undo_debt_entry(session, user.id, second.id)
    assert await get_person(session, user.id, person.id) is not None
    assert await get_person_balances(session, user.id, person.id) == {"UZS": -500_000}


async def test_undo_twice_or_for_someone_else_returns_none(session):
    user, other = await make_user(session, 1), await make_user(session, 2)
    person = await get_or_create_person(session, user.id, "Aziz", NOW)
    e = await entry(session, user, person, "borrowed", 100)
    assert await undo_debt_entry(session, other.id, e.id) is None
    assert await undo_debt_entry(session, user.id, e.id) is not None
    assert await undo_debt_entry(session, user.id, e.id) is None


async def test_last_debt_stamp(session):
    user = await make_user(session)
    assert await get_last_debt_stamp(session, user.id) is None
    person = await get_or_create_person(session, user.id, "Aziz", NOW)
    await entry(session, user, person, "lent", 1, hours=0)
    newest = await entry(session, user, person, "lent", 2, hours=3)
    assert await get_last_debt_stamp(session, user.id) == (newest.id, at(3))


async def test_effective_due_date_is_the_latest_dated_borrowed_or_lent_entry(session):
    user = await make_user(session)
    person = await get_or_create_person(session, user.id, "Aziz", NOW)
    assert await effective_due_date(session, user.id, person.id, "UZS") is None
    await entry(session, user, person, "borrowed", 100, hours=0, due=date(2026, 12, 1))
    await entry(session, user, person, "lent", 50, hours=1)  # no deadline: does not clear it
    assert await effective_due_date(session, user.id, person.id, "UZS") == date(2026, 12, 1)
    await entry(session, user, person, "borrowed", 100, hours=2, due=date(2026, 12, 15))
    assert await effective_due_date(session, user.id, person.id, "UZS") == date(2026, 12, 15)
    assert await effective_due_date(session, user.id, person.id, "USD") is None


async def test_change_due_date_edits_the_dated_entry(session):
    user = await make_user(session)
    person = await get_or_create_person(session, user.id, "Aziz", NOW)
    await entry(session, user, person, "borrowed", 100, hours=0, due=date(2026, 12, 1))
    await entry(session, user, person, "borrowed", 100, hours=1)  # newer, no date
    assert await set_due_date(session, user.id, person.id, "UZS", date(2026, 12, 31))
    assert await effective_due_date(session, user.id, person.id, "UZS") == date(2026, 12, 31)
    dues = [e.due_date for e in await entries_for_person(session, user.id, person.id)]
    assert dues == [None, date(2026, 12, 31)]  # newest first: only the dated one changed


async def test_set_due_date_when_nothing_has_a_date_uses_the_newest_entry(session):
    user = await make_user(session)
    person = await get_or_create_person(session, user.id, "Aziz", NOW)
    await entry(session, user, person, "borrowed", 100, hours=0)
    await entry(session, user, person, "borrowed", 100, hours=1)
    await set_due_date(session, user.id, person.id, "UZS", date(2026, 12, 31))
    dues = [e.due_date for e in await entries_for_person(session, user.id, person.id)]
    assert dues == [date(2026, 12, 31), None]


async def test_removing_the_deadline_and_currency_scope(session):
    user = await make_user(session)
    person = await get_or_create_person(session, user.id, "Aziz", NOW)
    await entry(session, user, person, "borrowed", 100, hours=0, due=date(2026, 12, 1))
    await entry(session, user, person, "borrowed", 5, currency="USD", hours=1, due=date(2026, 12, 2))
    await set_due_date(session, user.id, person.id, "UZS", None)
    assert await effective_due_date(session, user.id, person.id, "UZS") is None
    assert await effective_due_date(session, user.id, person.id, "USD") == date(2026, 12, 2)


async def test_close_debt_writes_the_entry_that_reaches_zero(session):
    user = await make_user(session)
    person = await get_or_create_person(session, user.id, "Aziz", NOW)
    await entry(session, user, person, "borrowed", 500_000)
    closing = await close_debt(session, user.id, person.id, "UZS", note="closed manually", now=at(1))
    assert (closing.kind, closing.amount, closing.note) == ("repaid_by_me", 500_000, "closed manually")
    assert await get_person_balances(session, user.id, person.id) == {"UZS": 0}
    assert await close_debt(session, user.id, person.id, "UZS") is None  # already closed
    assert await get_overview(session, user.id) == []  # hidden, but the history is kept
    assert len(await entries_for_person(session, user.id, person.id)) == 2


async def test_close_debt_owed_to_me(session):
    user = await make_user(session)
    person = await get_or_create_person(session, user.id, "Bobur", NOW)
    await entry(session, user, person, "lent", 300_000)
    closing = await close_debt(session, user.id, person.id, "UZS", now=at(1))
    assert (closing.kind, closing.amount) == ("repaid_to_me", 300_000)


async def test_delete_person_removes_the_whole_history(session):
    user, other = await make_user(session, 1), await make_user(session, 2)
    person = await get_or_create_person(session, user.id, "Aziz", NOW)
    await entry(session, user, person, "borrowed", 100)
    await entry(session, user, person, "repaid_by_me", 50, hours=1)
    assert await delete_person(session, other.id, person.id) is False  # not theirs
    assert await get_person(session, user.id, person.id) is not None
    assert await delete_person(session, user.id, person.id) is True
    assert await get_person(session, user.id, person.id) is None
    assert await session.scalar(select(func.count()).select_from(DebtEntry)) == 0
    assert await session.scalar(select(func.count()).select_from(Person)) == 0
