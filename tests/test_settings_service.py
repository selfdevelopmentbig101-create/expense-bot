from datetime import time

from app.services.settings import (
    set_currency,
    set_language,
    set_reminder_time,
    toggle_debt_reminders,
)
from app.services.users import get_or_create_user


async def test_currency_must_be_a_supported_one(session):
    user, _ = await get_or_create_user(session, 1, None)
    assert set_currency(user, "USD") is True and user.currency == "USD"
    assert set_currency(user, "XYZ") is False and user.currency == "USD"


async def test_language(session):
    user, _ = await get_or_create_user(session, 1, None)
    assert set_language(user, "uz") is True and user.language == "uz"
    assert set_language(user, "de") is False and user.language == "uz"


async def test_reminder_time_on_and_off(session):
    user, _ = await get_or_create_user(session, 1, None)
    await session.refresh(user)
    assert user.reminder_time is None  # off by default
    set_reminder_time(user, time(21, 30))
    await session.commit()
    await session.refresh(user)
    assert user.reminder_time == time(21, 30)
    set_reminder_time(user, None)
    assert user.reminder_time is None


async def test_debt_reminders_toggle(session):
    user, _ = await get_or_create_user(session, 1, None)
    assert user.debt_reminders_enabled is True
    assert toggle_debt_reminders(user) is False
    assert toggle_debt_reminders(user) is True
