"""Changing a user's settings. The caller commits."""
from datetime import time

from app.core.money import SUPPORTED_CURRENCIES
from app.db.models import User
from app.i18n import LANGUAGES


def set_currency(user: User, code: str) -> bool:
    if code not in SUPPORTED_CURRENCIES:
        return False
    user.currency = code
    return True


def set_language(user: User, code: str) -> bool:
    if code not in LANGUAGES:
        return False
    user.language = code
    return True


def set_reminder_time(user: User, value: time | None) -> None:
    """None switches the evening reminder off. A new time may fire again today."""
    user.reminder_time = value
    user.last_evening_reminded_on = None


def toggle_debt_reminders(user: User) -> bool:
    user.debt_reminders_enabled = not user.debt_reminders_enabled
    return user.debt_reminders_enabled
