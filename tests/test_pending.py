from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.db.models import PendingAction
from app.services.pending import (
    PENDING_TTL,
    PendingState,
    consume_pending,
    create_pending,
    get_pending,
    purge_expired,
)
from app.services.users import get_or_create_user

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)
PAYLOAD = {"amount": 10000, "currency": "UZS", "type": "expense", "note": None}


async def new_user(session, telegram_id=1):
    user, _ = await get_or_create_user(session, telegram_id, None)
    return user


async def test_create_then_get(session):
    user = await new_user(session)
    created = await create_pending(session, user.id, PendingState.CHOOSE_CATEGORY, PAYLOAD, NOW)
    found = await get_pending(session, user.id, created.token, NOW)
    assert found is not None
    assert found.state is PendingState.CHOOSE_CATEGORY
    assert found.payload == PAYLOAD


async def test_a_new_amount_replaces_the_old_one(session):
    user = await new_user(session)
    first = await create_pending(session, user.id, PendingState.CHOOSE_CATEGORY, PAYLOAD, NOW)
    second = await create_pending(session, user.id, PendingState.CHOOSE_CATEGORY, PAYLOAD, NOW)
    assert await get_pending(session, user.id, first.token, NOW) is None
    assert await get_pending(session, user.id, second.token, NOW) is not None
    count = await session.scalar(select(func.count()).select_from(PendingAction))
    assert count == 1


async def test_expires_after_ten_minutes(session):
    user = await new_user(session)
    pending = await create_pending(session, user.id, PendingState.CHOOSE_CATEGORY, PAYLOAD, NOW)
    assert PENDING_TTL == timedelta(minutes=10)
    assert await get_pending(session, user.id, pending.token, NOW + timedelta(minutes=9, seconds=59))
    assert await get_pending(session, user.id, pending.token, NOW + timedelta(minutes=10, seconds=1)) is None
    assert await consume_pending(session, user.id, pending.token, NOW + timedelta(minutes=11)) is None


async def test_consume_works_only_once(session):
    user = await new_user(session)
    pending = await create_pending(session, user.id, PendingState.CHOOSE_CATEGORY, PAYLOAD, NOW)
    assert await consume_pending(session, user.id, pending.token, NOW) is not None
    assert await consume_pending(session, user.id, pending.token, NOW) is None  # double tap
    assert await get_pending(session, user.id, pending.token, NOW) is None


async def test_other_users_cannot_use_a_token(session):
    alice = await new_user(session, 1)
    bob = await new_user(session, 2)
    pending = await create_pending(session, alice.id, PendingState.CHOOSE_CATEGORY, PAYLOAD, NOW)
    assert await get_pending(session, bob.id, pending.token, NOW) is None
    assert await consume_pending(session, bob.id, pending.token, NOW) is None
    assert await get_pending(session, alice.id, pending.token, NOW) is not None


async def test_users_do_not_replace_each_others_pending(session):
    alice = await new_user(session, 1)
    bob = await new_user(session, 2)
    a = await create_pending(session, alice.id, PendingState.CHOOSE_CATEGORY, PAYLOAD, NOW)
    await create_pending(session, bob.id, PendingState.CHOOSE_CATEGORY, PAYLOAD, NOW)
    assert await get_pending(session, alice.id, a.token, NOW) is not None


async def test_purge_expired(session):
    user = await new_user(session)
    await create_pending(session, user.id, PendingState.CHOOSE_CATEGORY, PAYLOAD, NOW)
    assert await purge_expired(session, NOW + timedelta(minutes=5)) == 0
    assert await purge_expired(session, NOW + timedelta(minutes=11)) == 1
