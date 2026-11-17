"""Odd data must be stored and read back unchanged, and never break a query."""
from datetime import datetime, timezone

from app.db.seed import seed_default_categories
from app.services.categories import add_category, list_categories
from app.services.debts import add_debt_entry, get_or_create_person, get_person_balances
from app.services.transactions import all_transactions, save_transaction
from app.services.users import get_or_create_user

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)

HOSTILE = [
    "'; DROP TABLE users; --",
    '"quoted" and \'single\'',
    "<script>alert(1)</script> & <b>bold</b>",
    "\U0001F35E\U0001F680 emoji \u2764\ufe0f",
    "\u0627\u0644\u0639\u0631\u0628\u064a\u0629 \u05e2\u05d1\u05e8\u05d9\u05ea",  # right-to-left scripts
    "line one\nline two\ttabbed",
    "x" * 4000,
    "=HYPERLINK(\"http://evil\")",
]


async def test_a_huge_telegram_id_fits(session):
    user, created = await get_or_create_user(session, 9_876_543_210, "uz")
    assert created and user.telegram_id == 9_876_543_210
    await session.commit()
    again, created = await get_or_create_user(session, 9_876_543_210, "uz")
    assert not created and again.id == user.id


async def test_hostile_notes_are_stored_as_plain_data(session):
    await seed_default_categories(session)
    user, _ = await get_or_create_user(session, 1, None)
    food = (await list_categories(session, user.id, "expense"))[0]
    for index, note in enumerate(HOSTILE):
        await save_transaction(session, user_id=user.id, category_id=food.id, entry_type="expense",
                               amount=index + 1, currency="UZS", note=note, now=NOW)
    await session.commit()
    stored = [row.note for row in await all_transactions(session, user.id)]
    assert stored == HOSTILE
    assert await get_or_create_user(session, 1, None)  # the users table is still there


async def test_hostile_category_and_person_names(session):
    await seed_default_categories(session)
    user, _ = await get_or_create_user(session, 1, None)
    status, category = await add_category(session, user.id, "expense", "\U0001F9E8 '); DROP TABLE x;--")
    assert category is not None and category.name == "'); DROP TABLE x;--"
    person = await get_or_create_person(session, user.id, "  O'Brien  \u202e  ", NOW)
    await add_debt_entry(session, user_id=user.id, person_id=person.id, kind="lent", amount=1,
                         currency="UZS", note=HOSTILE[2], now=NOW)
    assert await get_person_balances(session, user.id, person.id) == {"UZS": 1}


async def test_the_largest_allowed_amount_fits_the_database(session):
    await seed_default_categories(session)
    user, _ = await get_or_create_user(session, 1, None)
    food = (await list_categories(session, user.id, "expense"))[0]
    biggest = 10**12 * 100  # 1 trillion dollars in cents: the parser's maximum
    await save_transaction(session, user_id=user.id, category_id=food.id, entry_type="expense",
                           amount=biggest, currency="USD", note=None, now=NOW)
    await session.commit()
    assert (await all_transactions(session, user.id))[0].amount == biggest
