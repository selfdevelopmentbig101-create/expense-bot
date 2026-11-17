"""The last step of the debt flow, without Telegram."""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select

from app.db.models import DebtEntry
from app.db.seed import seed_default_categories
from app.services.categories import list_categories
from app.services.debt_flow import DebtStatus, finalize_debt
from app.services.debts import (
    add_debt_entry,
    get_or_create_person,
    get_overview,
    get_person,
    get_person_balances,
)
from app.services.pending import PendingState, create_pending, get_pending
from app.services.transactions import list_between, save_transaction, totals_between
from app.services.undo import undo_last
from app.services.users import get_or_create_user
from app.utils.timezone import local_day_bounds

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)


async def make_user(session, telegram_id=1):
    user, _ = await get_or_create_user(session, telegram_id, None)
    return user


async def pend(session, user, state=PendingState.DEBT_DUE, **payload):
    base = {"flow": "debt", "amount": 500_000, "currency": "UZS", "type": "expense", "note": None}
    return await create_pending(session, user.id, state, {**base, **payload}, NOW)


async def owe(session, user, name="Aziz", amount=500_000, kind="borrowed", currency="UZS"):
    """Set up an existing debt directly in the database."""
    person = await get_or_create_person(session, user.id, name, NOW - timedelta(days=1))
    await add_debt_entry(
        session, user_id=user.id, person_id=person.id, kind=kind, amount=amount,
        currency=currency, now=NOW - timedelta(days=1),
    )
    return person


async def entry_count(session):
    return await session.scalar(select(func.count()).select_from(DebtEntry))


async def test_borrowed_from_a_new_person(session):
    user = await make_user(session)
    p = await pend(session, user, kind="borrowed", person_name="Aziz", due="2026-11-25", note="rent")
    out = await finalize_debt(session, user, p.token, now=NOW)
    assert out.status is DebtStatus.SAVED
    assert (out.person_name, out.kind, out.amount, out.currency) == ("Aziz", "borrowed", 500_000, "UZS")
    assert out.balance == -500_000
    assert out.due == date(2026, 11, 25)
    assert (out.entry.note, out.entry.due_date) == ("rent", date(2026, 11, 25))
    assert await get_pending(session, user.id, p.token, NOW) is None  # used up


async def test_lent_to_an_existing_person_by_id(session):
    user = await make_user(session)
    person = await owe(session, user, "Bobur", 100_000, kind="lent")
    p = await pend(session, user, kind="lent", person_id=person.id, person_name="Bobur", amount=50_000)
    out = await finalize_debt(session, user, p.token, now=NOW)
    assert out.status is DebtStatus.SAVED and out.balance == 150_000


async def test_a_typed_name_finds_the_existing_person_case_insensitively(session):
    user = await make_user(session)
    person = await owe(session, user, "Aziz", 100_000)
    p = await pend(session, user, kind="borrowed", person_name="  aZIZ ", amount=50_000)
    out = await finalize_debt(session, user, p.token, now=NOW)
    assert out.status is DebtStatus.SAVED
    assert out.person_name == "Aziz" and out.balance == -150_000
    assert [s.person_id for s in [out.entry]] == [person.id]  # no duplicate person


async def test_double_tap_saves_the_debt_only_once(session):
    user = await make_user(session)
    p = await pend(session, user, kind="borrowed", person_name="Aziz")
    first = await finalize_debt(session, user, p.token, now=NOW)
    second = await finalize_debt(session, user, p.token, now=NOW)
    assert first.status is DebtStatus.SAVED and second.status is DebtStatus.STALE
    assert await entry_count(session) == 1


async def test_expired_or_foreign_pending_saves_nothing(session):
    user, other = await make_user(session, 1), await make_user(session, 2)
    p = await pend(session, user, kind="borrowed", person_name="Aziz")
    late = NOW + timedelta(minutes=11)
    assert (await finalize_debt(session, user, p.token, now=late)).status is DebtStatus.STALE
    assert (await finalize_debt(session, other, p.token, now=NOW)).status is DebtStatus.STALE
    assert await entry_count(session) == 0


async def test_a_category_pending_is_not_a_debt(session):
    user = await make_user(session)
    p = await create_pending(session, user.id, PendingState.CHOOSE_CATEGORY,
                             {"amount": 1, "currency": "UZS", "kind": "borrowed", "person_name": "A"}, NOW)
    assert (await finalize_debt(session, user, p.token, now=NOW)).status is DebtStatus.STALE


async def test_incomplete_or_foreign_person_is_rejected(session):
    user, other = await make_user(session, 1), await make_user(session, 2)
    no_person = await pend(session, user, kind="borrowed")
    assert (await finalize_debt(session, user, no_person.token, now=NOW)).status is DebtStatus.BAD
    theirs = await owe(session, other, "Secret")
    foreign = await pend(session, user, kind="borrowed", person_id=theirs.id, person_name="Secret")
    assert (await finalize_debt(session, user, foreign.token, now=NOW)).status is DebtStatus.BAD
    assert await entry_count(session) == 1  # only the other user's setup entry


async def test_partial_repayment(session):
    user = await make_user(session)
    person = await owe(session, user, "Aziz", 500_000)
    p = await pend(session, user, PendingState.DEBT_PERSON, kind="repaid_by_me",
                   person_id=person.id, person_name="Aziz", amount=200_000)
    out = await finalize_debt(session, user, p.token, now=NOW)
    assert out.status is DebtStatus.SAVED and out.balance == -300_000


async def test_full_repayment_closes_the_debt_and_hides_it(session):
    user = await make_user(session)
    person = await owe(session, user, "Bobur", 300_000, kind="lent")
    p = await pend(session, user, PendingState.DEBT_PERSON, kind="repaid_to_me",
                   person_id=person.id, person_name="Bobur", amount=300_000)
    out = await finalize_debt(session, user, p.token, now=NOW)
    assert out.status is DebtStatus.SAVED and out.balance == 0
    assert await get_overview(session, user.id) == []
    assert await get_person(session, user.id, person.id) is not None  # kept in history


async def test_repayment_larger_than_the_debt_asks_for_confirmation(session):
    user = await make_user(session)
    person = await owe(session, user, "Aziz", 100_000)
    p = await pend(session, user, PendingState.DEBT_PERSON, kind="repaid_by_me",
                   person_id=person.id, person_name="Aziz", amount=150_000)
    out = await finalize_debt(session, user, p.token, now=NOW)
    assert out.status is DebtStatus.CONFIRM_OVERPAY
    assert (out.owed, out.rest) == (100_000, 50_000)
    assert (await get_pending(session, user.id, p.token, NOW)).state is PendingState.DEBT_CONFIRM
    assert await get_person_balances(session, user.id, person.id) == {"UZS": -100_000}  # untouched

    forced = await finalize_debt(session, user, p.token, force=True, now=NOW)
    assert forced.status is DebtStatus.SAVED and forced.balance == 50_000  # now Aziz owes me


async def test_force_and_as_debt_only_work_from_the_matching_confirmation(session):
    user = await make_user(session)
    person = await owe(session, user, "Aziz", 100_000)
    p = await pend(session, user, PendingState.DEBT_PERSON, kind="repaid_by_me",
                   person_id=person.id, person_name="Aziz", amount=150_000)
    assert (await finalize_debt(session, user, p.token, force=True, now=NOW)).status is DebtStatus.STALE
    assert (await finalize_debt(session, user, p.token, as_debt=True, now=NOW)).status is DebtStatus.STALE
    await finalize_debt(session, user, p.token, now=NOW)  # -> over confirmation
    assert (await finalize_debt(session, user, p.token, as_debt=True, now=NOW)).status is DebtStatus.STALE
    assert await entry_count(session) == 1


async def test_repayment_without_any_debt_warns_and_can_become_a_new_debt(session):
    user = await make_user(session)
    p = await pend(session, user, PendingState.DEBT_PERSON, kind="repaid_by_me",
                   person_name="Aziz", amount=200_000)
    warn = await finalize_debt(session, user, p.token, now=NOW)
    assert warn.status is DebtStatus.CONFIRM_NO_DEBT
    assert await entry_count(session) == 0 and await get_person(session, user.id, 1) is None

    done = await finalize_debt(session, user, p.token, as_debt=True, now=NOW)
    assert done.status is DebtStatus.SAVED
    assert done.entry.kind == "lent" and done.balance == 200_000  # "I repaid" -> I lent


async def test_they_repaid_me_without_a_debt_becomes_borrowed(session):
    user = await make_user(session)
    p = await pend(session, user, PendingState.DEBT_PERSON, kind="repaid_to_me",
                   person_name="Bobur", amount=70_000)
    assert (await finalize_debt(session, user, p.token, now=NOW)).status is DebtStatus.CONFIRM_NO_DEBT
    done = await finalize_debt(session, user, p.token, as_debt=True, now=NOW)
    assert done.entry.kind == "borrowed" and done.balance == -70_000


async def test_repayment_in_the_wrong_direction_has_no_matching_debt(session):
    user = await make_user(session)
    person = await owe(session, user, "Aziz", 100_000)  # I owe Aziz
    p = await pend(session, user, PendingState.DEBT_PERSON, kind="repaid_to_me",
                   person_id=person.id, person_name="Aziz", amount=10_000)
    assert (await finalize_debt(session, user, p.token, now=NOW)).status is DebtStatus.CONFIRM_NO_DEBT


async def test_currencies_are_never_mixed(session):
    user = await make_user(session)
    person = await owe(session, user, "Aziz", 500_000, currency="UZS")
    p = await pend(session, user, PendingState.DEBT_PERSON, kind="repaid_by_me",
                   person_id=person.id, person_name="Aziz", amount=5_000, currency="USD")
    out = await finalize_debt(session, user, p.token, now=NOW)
    assert out.status is DebtStatus.CONFIRM_NO_DEBT  # no USD debt, only a UZS one
    assert await get_person_balances(session, user.id, person.id) == {"UZS": -500_000}


async def test_a_repayment_has_no_due_date(session):
    user = await make_user(session)
    person = await owe(session, user, "Aziz", 500_000)
    p = await pend(session, user, PendingState.DEBT_PERSON, kind="repaid_by_me",
                   person_id=person.id, person_name="Aziz", amount=1_000, due="2026-12-01")
    out = await finalize_debt(session, user, p.token, now=NOW)
    assert out.entry.due_date is None


async def test_typed_amount_from_the_debts_screen_is_applied_as_an_override(session):
    user = await make_user(session)
    person = await owe(session, user, "Aziz", 500_000)
    p = await create_pending(
        session, user.id, PendingState.DEBT_REPAY_AMOUNT,
        {"flow": "debt", "mode": "person", "kind": "repaid_by_me", "person_id": person.id,
         "person_name": "Aziz", "currency": "UZS", "owed": 500_000}, NOW,
    )
    out = await finalize_debt(session, user, p.token, overrides={"amount": 120_000, "note": "part"}, now=NOW)
    assert out.status is DebtStatus.SAVED and out.balance == -380_000 and out.entry.note == "part"


async def test_debts_never_show_up_in_expense_or_income_totals(session):
    user = await make_user(session)
    p = await pend(session, user, kind="borrowed", person_name="Aziz", amount=500_000)
    await finalize_debt(session, user, p.token, now=NOW)
    start, end = local_day_bounds(NOW, user.timezone)
    assert await totals_between(session, user.id, "expense", start, end) == {}
    assert await totals_between(session, user.id, "income", start, end) == {}
    assert await list_between(session, user.id, start, end) == []


async def test_the_entry_carries_the_idempotency_key(session):
    user = await make_user(session)
    p = await pend(session, user, kind="lent", person_name="Aziz")
    await finalize_debt(session, user, p.token, now=NOW)
    key = await session.scalar(select(DebtEntry.idempotency_key))
    assert key == f"pending:{p.token}"


async def test_undo_last_picks_the_newest_record_of_any_kind(session):
    await seed_default_categories(session)
    user = await make_user(session)
    food = (await list_categories(session, user.id, "expense"))[0]
    await save_transaction(session, user_id=user.id, category_id=food.id, entry_type="expense",
                           amount=1_000, currency="UZS", note=None, now=NOW)
    p = await pend(session, user, kind="borrowed", person_name="Aziz")
    await finalize_debt(session, user, p.token, now=NOW + timedelta(minutes=5))

    first = await undo_last(session, user.id)
    assert first.debt is not None and first.debt.person_name == "Aziz"
    assert await get_person(session, user.id, first.debt.person_id) is None  # orphan removed
    second = await undo_last(session, user.id)
    assert second.transaction is not None and second.transaction.amount == 1_000
    assert await undo_last(session, user.id) is None
