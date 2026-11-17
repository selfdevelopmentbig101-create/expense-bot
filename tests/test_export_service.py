import csv
import io
from datetime import date, datetime, timezone

from app.db.seed import seed_default_categories
from app.services.categories import list_categories
from app.services.debts import add_debt_entry, get_or_create_person
from app.services.export import export_debts_csv, export_transactions_csv
from app.services.transactions import save_transaction
from app.services.users import get_or_create_user

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)  # 17:00 in Tashkent


def rows(data: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(data.decode("utf-8-sig"), newline=""), delimiter=";"))


async def setup(session, telegram_id=1, language=None):
    await seed_default_categories(session)
    user, _ = await get_or_create_user(session, telegram_id, language)
    return user, await list_categories(session, user.id, "expense"), await list_categories(session, user.id, "income")


async def test_nothing_to_export(session):
    user, _, _ = await setup(session)
    assert await export_transactions_csv(session, user) is None
    assert await export_debts_csv(session, user) is None


async def test_transactions_csv_has_a_bom_translated_headers_and_local_times(session):
    user, expense, income = await setup(session)
    await save_transaction(session, user_id=user.id, category_id=expense[0].id, entry_type="expense",
                           amount=10_000, currency="UZS", note="bread", now=NOW)
    await save_transaction(session, user_id=user.id, category_id=income[0].id, entry_type="income",
                           amount=2_000_000, currency="UZS", note=None, now=NOW.replace(hour=13))
    data = await export_transactions_csv(session, user)
    assert data.startswith(b"\xef\xbb\xbf")
    assert rows(data) == [
        ["Date", "Type", "Category", "Amount", "Currency", "Note"],
        ["2026-11-17 17:00", "Expense", "Food", "10000", "UZS", "bread"],
        ["2026-11-17 18:00", "Income", "Salary", "2000000", "UZS", ""],
    ]


async def test_export_follows_the_users_language_and_keeps_cyrillic_intact(session):
    user, expense, _ = await setup(session, language="ru")
    await save_transaction(session, user_id=user.id, category_id=expense[0].id, entry_type="expense",
                           amount=1_000, currency="UZS", note="\u0445\u043b\u0435\u0431; \"\u0441\u0432\u0435\u0436\u0438\u0439\"", now=NOW)
    table = rows(await export_transactions_csv(session, user))
    assert table[0][0] == "\u0414\u0430\u0442\u0430"
    assert table[1][1:3] == ["\u0420\u0430\u0441\u0445\u043e\u0434", "\u0415\u0434\u0430"]
    assert table[1][5] == "\u0445\u043b\u0435\u0431; \"\u0441\u0432\u0435\u0436\u0438\u0439\""


async def test_cents_use_a_decimal_comma_and_formulas_are_neutralized(session):
    user, expense, _ = await setup(session)
    await save_transaction(session, user_id=user.id, category_id=expense[0].id, entry_type="expense",
                           amount=5_050, currency="USD", note="=HYPERLINK(\"http://x\")", now=NOW)
    row = rows(await export_transactions_csv(session, user))[1]
    assert row[3] == "50,50" and row[4] == "USD"
    assert row[5].startswith("'=")


async def test_records_come_oldest_first(session):
    user, expense, _ = await setup(session)
    for minutes, amount in ((30, 3), (0, 1), (10, 2)):
        await save_transaction(session, user_id=user.id, category_id=expense[0].id, entry_type="expense",
                               amount=amount, currency="UZS", note=None, now=NOW.replace(minute=minutes))
    assert [r[3] for r in rows(await export_transactions_csv(session, user))[1:]] == ["1", "2", "3"]


async def test_debts_are_a_separate_file_with_the_balance_change(session):
    user, expense, _ = await setup(session)
    aziz = await get_or_create_person(session, user.id, "Aziz", NOW)
    await add_debt_entry(session, user_id=user.id, person_id=aziz.id, kind="borrowed", amount=500_000,
                         currency="UZS", due_date=date(2026, 11, 25), note="rent", now=NOW)
    await add_debt_entry(session, user_id=user.id, person_id=aziz.id, kind="repaid_by_me", amount=200_000,
                         currency="UZS", now=NOW.replace(hour=13))
    assert await export_transactions_csv(session, user) is None  # debts are not income or expenses
    assert rows(await export_debts_csv(session, user)) == [
        ["Date", "Person", "Kind", "Amount", "Currency", "Balance change (+ owed to me, - I owe)", "Due date", "Note"],
        ["2026-11-17 17:00", "Aziz", "Borrowed", "500000", "UZS", "-500000", "2026-11-25", "rent"],
        ["2026-11-17 18:00", "Aziz", "Repaid by me", "200000", "UZS", "200000", "", ""],
    ]


async def test_export_is_isolated_between_users(session):
    user, expense, _ = await setup(session)
    other, _ = await get_or_create_user(session, 2, None)
    await save_transaction(session, user_id=user.id, category_id=expense[0].id, entry_type="expense",
                           amount=1, currency="UZS", note=None, now=NOW)
    assert await export_transactions_csv(session, other) is None
