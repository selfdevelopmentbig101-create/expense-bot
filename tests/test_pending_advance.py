from datetime import datetime, timedelta, timezone

from app.services.pending import (
    PENDING_TTL,
    TEXT_STATES,
    PendingState,
    advance_pending,
    create_pending,
    get_current_pending,
    get_pending,
)
from app.services.users import get_or_create_user

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)


async def start(session, telegram_id=1):
    user, _ = await get_or_create_user(session, telegram_id, None)
    pending = await create_pending(session, user.id, PendingState.CHOOSE_CATEGORY, {"a": 1}, NOW)
    return user, pending


async def test_advance_changes_state_and_payload(session):
    user, p = await start(session)
    moved = await advance_pending(
        session, user.id, p.token, expected=PendingState.CHOOSE_CATEGORY,
        new_state=PendingState.DEBT_KIND, payload={"a": 1, "b": 2}, now=NOW,
    )
    assert moved is not None
    again = await get_pending(session, user.id, p.token, NOW)
    assert again.state is PendingState.DEBT_KIND and again.payload == {"a": 1, "b": 2}


async def test_a_double_tap_cannot_advance_twice(session):
    user, p = await start(session)
    first = await advance_pending(
        session, user.id, p.token, expected=PendingState.CHOOSE_CATEGORY,
        new_state=PendingState.DEBT_KIND, payload={}, now=NOW,
    )
    second = await advance_pending(
        session, user.id, p.token, expected=PendingState.CHOOSE_CATEGORY,
        new_state=PendingState.DEBT_KIND, payload={}, now=NOW,
    )
    assert first is not None and second is None


async def test_every_step_restarts_the_ten_minute_timer(session):
    user, p = await start(session)
    later = NOW + timedelta(minutes=9)
    await advance_pending(
        session, user.id, p.token, expected=PendingState.CHOOSE_CATEGORY,
        new_state=PendingState.DEBT_KIND, payload={}, now=later,
    )
    still_alive = later + timedelta(minutes=9)  # 18 minutes after the start
    assert await get_pending(session, user.id, p.token, still_alive) is not None
    assert await get_pending(session, user.id, p.token, later + PENDING_TTL + timedelta(seconds=1)) is None


async def test_cannot_advance_an_expired_or_foreign_pending(session):
    user, p = await start(session)
    other, _ = await get_or_create_user(session, 2, None)
    late = NOW + timedelta(minutes=11)
    assert await advance_pending(
        session, user.id, p.token, expected=PendingState.CHOOSE_CATEGORY,
        new_state=PendingState.DEBT_KIND, payload={}, now=late,
    ) is None
    assert await advance_pending(
        session, other.id, p.token, expected=PendingState.CHOOSE_CATEGORY,
        new_state=PendingState.DEBT_KIND, payload={}, now=NOW,
    ) is None


async def test_current_pending_is_the_users_live_one(session):
    user, p = await start(session)
    assert (await get_current_pending(session, user.id, NOW)).token == p.token
    assert await get_current_pending(session, user.id, NOW + timedelta(minutes=11)) is None
    other, _ = await get_or_create_user(session, 2, None)
    assert await get_current_pending(session, other.id, NOW) is None


def test_text_states_are_the_ones_that_wait_for_typed_text():
    assert TEXT_STATES == {
        PendingState.DEBT_NEW_NAME,
        PendingState.DEBT_DUE_TEXT,
        PendingState.DEBT_REPAY_AMOUNT,
        PendingState.CAT_ADD_NAME,
        PendingState.CAT_RENAME_NAME,
        PendingState.BUDGET_AMOUNT,
        PendingState.SETTINGS_TIME,
    }
