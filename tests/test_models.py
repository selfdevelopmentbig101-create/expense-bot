from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.db.models import Category, Person, Transaction, User
from app.db.types import UTCDateTime, utcnow


def test_naive_datetime_is_rejected():
    with pytest.raises(ValueError):
        UTCDateTime().process_bind_param(datetime(2026, 1, 1), None)


def test_datetime_is_stored_as_utc():
    tashkent = timezone(timedelta(hours=5))
    stored = UTCDateTime().process_bind_param(datetime(2026, 1, 1, 12, 0, tzinfo=tashkent), None)
    assert stored == datetime(2026, 1, 1, 7, 0)  # naive UTC
    back = UTCDateTime().process_result_value(stored, None)
    assert back.tzinfo == timezone.utc


async def test_created_at_round_trips_as_aware_utc(session):
    user = User(telegram_id=5)
    session.add(user)
    await session.commit()
    session.expire_all()
    loaded = await session.scalar(select(User).where(User.telegram_id == 5))
    assert loaded.created_at.tzinfo == timezone.utc
    assert abs(utcnow() - loaded.created_at) < timedelta(minutes=1)


async def test_person_names_are_unique_per_user(session):
    u1, u2 = User(telegram_id=1), User(telegram_id=2)
    session.add_all([u1, u2])
    await session.flush()
    session.add(Person(user_id=u1.id, name="Aziz", name_normalized="aziz"))
    session.add(Person(user_id=u2.id, name="Aziz", name_normalized="aziz"))  # other user: ok
    await session.flush()
    session.add(Person(user_id=u1.id, name=" AZIZ ", name_normalized="aziz"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_amount_must_be_positive(session):
    user = User(telegram_id=1)
    cat = Category(name="Food", type="expense")
    session.add_all([user, cat])
    await session.flush()
    session.add(Transaction(user_id=user.id, category_id=cat.id, type="expense", amount=0, currency="UZS"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_deleting_a_user_removes_their_data(session):
    user = User(telegram_id=1)
    cat = Category(name="Food", type="expense")
    session.add_all([user, cat])
    await session.flush()
    session.add(Transaction(user_id=user.id, category_id=cat.id, type="expense", amount=100, currency="UZS"))
    await session.commit()

    await session.delete(user)
    await session.commit()
    count = await session.scalar(select(func.count()).select_from(Transaction))
    assert count == 0  # needs PRAGMA foreign_keys=ON from create_engine
