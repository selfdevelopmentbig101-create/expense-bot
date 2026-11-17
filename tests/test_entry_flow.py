"""The whole second step: category tap -> saved record (without Telegram)."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.db.models import Category, Transaction
from app.db.seed import seed_default_categories
from app.services.categories import list_categories
from app.services.entry_flow import save_chosen_category
from app.services.pending import PendingState, create_pending
from app.services.transactions import undo_transaction
from app.services.users import get_or_create_user

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)


async def setup(session):
    await seed_default_categories(session)
    user, _ = await get_or_create_user(session, 1, None)
    expense = await list_categories(session, user.id, "expense")
    income = await list_categories(session, user.id, "income")
    await session.commit()
    return user, expense, income


async def pend(session, user, amount=10000, currency="UZS", entry_type="expense", note="bread",
               state=PendingState.CHOOSE_CATEGORY):
    payload = {"amount": amount, "currency": currency, "type": entry_type, "note": note}
    return await create_pending(session, user.id, state, payload, NOW)


async def count(session):
    return await session.scalar(select(func.count()).select_from(Transaction))


async def test_tapping_a_category_saves_the_pending_amount(session):
    user, expense, _ = await setup(session)
    pending = await pend(session, user)
    saved = await save_chosen_category(session, user, pending.token, expense[0].id, NOW)
    assert saved is not None
    assert (saved.amount, saved.currency, saved.type, saved.note) == (10000, "UZS", "expense", "bread")
    assert saved.category_name == "Food"
    assert saved.total_today == 10000
    assert await count(session) == 1


async def test_double_tap_saves_only_once(session):
    user, expense, _ = await setup(session)
    pending = await pend(session, user)
    first = await save_chosen_category(session, user, pending.token, expense[0].id, NOW)
    second = await save_chosen_category(session, user, pending.token, expense[0].id, NOW)
    assert first is not None and second is None
    assert await count(session) == 1


async def test_tapping_two_different_categories_saves_only_once(session):
    user, expense, _ = await setup(session)
    pending = await pend(session, user)
    await save_chosen_category(session, user, pending.token, expense[0].id, NOW)
    assert await save_chosen_category(session, user, pending.token, expense[1].id, NOW) is None
    assert await count(session) == 1


async def test_expired_pending_saves_nothing(session):
    user, expense, _ = await setup(session)
    pending = await pend(session, user)
    late = NOW + timedelta(minutes=10, seconds=1)
    assert await save_chosen_category(session, user, pending.token, expense[0].id, late) is None
    assert await count(session) == 0


async def test_a_new_amount_invalidates_the_old_keyboard(session):
    user, expense, _ = await setup(session)
    old = await pend(session, user, amount=1000)
    new = await pend(session, user, amount=2000)
    assert await save_chosen_category(session, user, old.token, expense[0].id, NOW) is None
    saved = await save_chosen_category(session, user, new.token, expense[0].id, NOW)
    assert saved is not None and saved.amount == 2000


async def test_income_uses_income_categories_only(session):
    user, expense, income = await setup(session)
    pending = await pend(session, user, amount=2000000, entry_type="income", note=None)
    assert await save_chosen_category(session, user, pending.token, expense[0].id, NOW) is None
    saved = await save_chosen_category(session, user, pending.token, income[0].id, NOW)
    assert saved is not None
    assert (saved.type, saved.category_name) == ("income", "Salary")


async def test_expense_cannot_go_to_an_income_category(session):
    user, _, income = await setup(session)
    pending = await pend(session, user)
    assert await save_chosen_category(session, user, pending.token, income[0].id, NOW) is None
    assert await count(session) == 0


async def test_other_users_category_and_archived_category_are_refused(session):
    user, expense, _ = await setup(session)
    other, _ = await get_or_create_user(session, 2, None)
    theirs = Category(user_id=other.id, name="Secret", emoji="x", type="expense")
    archived = Category(user_id=user.id, name="Old", emoji="x", type="expense", is_archived=True)
    session.add_all([theirs, archived])
    await session.flush()

    pending = await pend(session, user)
    assert await save_chosen_category(session, user, pending.token, theirs.id, NOW) is None
    assert await save_chosen_category(session, user, pending.token, archived.id, NOW) is None
    assert await save_chosen_category(session, user, pending.token, 99999, NOW) is None
    assert await count(session) == 0
    # the pending action is still alive: a valid tap afterwards works
    assert await save_chosen_category(session, user, pending.token, expense[0].id, NOW) is not None


async def test_wrong_pending_state_cannot_be_saved(session):
    user, expense, _ = await setup(session)
    pending = await pend(session, user, state=PendingState.CONFIRM_LARGE)
    assert await save_chosen_category(session, user, pending.token, expense[0].id, NOW) is None
    assert await count(session) == 0


async def test_someone_elses_token_does_nothing(session):
    user, expense, _ = await setup(session)
    other, _ = await get_or_create_user(session, 2, None)
    pending = await pend(session, user)
    assert await save_chosen_category(session, other, pending.token, expense[0].id, NOW) is None
    assert await count(session) == 0


async def test_total_today_adds_up_and_ignores_other_currencies(session):
    user, expense, income = await setup(session)
    p1 = await pend(session, user, amount=10000)
    await save_chosen_category(session, user, p1.token, expense[0].id, NOW)
    p2 = await pend(session, user, amount=5000, currency="USD")
    usd = await save_chosen_category(session, user, p2.token, expense[0].id, NOW)
    p3 = await pend(session, user, amount=35000)
    uzs = await save_chosen_category(session, user, p3.token, expense[1].id, NOW)
    p4 = await pend(session, user, amount=999999, entry_type="income", note=None)
    await save_chosen_category(session, user, p4.token, income[0].id, NOW)

    assert usd.total_today == 5000
    assert uzs.total_today == 45000  # income and USD are not mixed in


async def test_undo_after_saving_restores_the_total(session):
    user, expense, _ = await setup(session)
    p1 = await pend(session, user, amount=10000)
    await save_chosen_category(session, user, p1.token, expense[0].id, NOW)
    p2 = await pend(session, user, amount=35000)
    second = await save_chosen_category(session, user, p2.token, expense[1].id, NOW)
    assert second.total_today == 45000

    assert await undo_transaction(session, user.id, second.transaction_id) is not None
    p3 = await pend(session, user, amount=1000)
    third = await save_chosen_category(session, user, p3.token, expense[0].id, NOW)
    assert third.total_today == 11000  # 10 000 + 1 000, the undone 35 000 is gone
