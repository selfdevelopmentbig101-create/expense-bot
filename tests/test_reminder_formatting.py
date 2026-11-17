from datetime import date

import pytest

from app.core.reminders import ReminderKind
from app.services.reminder_formatting import render_debt_reminder, render_evening
from app.services.reminders import DebtReminder, EveningReminder


def reminder(kind, balance, name="Aziz", currency="UZS", lang="en"):
    return DebtReminder(1, 1, lang, 1, name, currency, balance, date(2026, 11, 25), kind, 1, date(2026, 11, 24))


def test_the_examples_from_the_spec():
    assert render_debt_reminder("en", reminder(ReminderKind.TOMORROW, -500_000)) == (
        "\u23f0 Tomorrow you should return 500 000 UZS to Aziz."
    )
    assert render_debt_reminder("en", reminder(ReminderKind.TODAY, 200_000, "Bobur")) == (
        "\u23f0 Today Bobur should return 200 000 UZS to you."
    )


def test_both_directions_and_all_kinds():
    assert "Tomorrow Bobur should return 1 000 UZS to you" in render_debt_reminder("en", reminder(ReminderKind.TOMORROW, 1_000, "Bobur"))
    assert "Today you should return 1 000 UZS to Aziz" in render_debt_reminder("en", reminder(ReminderKind.TODAY, -1_000))
    assert "Overdue since 25.11.2026: you owe Aziz 1 000 UZS" in render_debt_reminder("en", reminder(ReminderKind.OVERDUE, -1_000))
    assert "Overdue since 25.11.2026: Bobur owes you 1 000 UZS" in render_debt_reminder("en", reminder(ReminderKind.OVERDUE, 1_000, "Bobur"))


def test_the_amount_is_the_current_open_balance_in_its_own_currency():
    text = render_debt_reminder("en", reminder(ReminderKind.TODAY, -5_000, currency="USD"))
    assert "50 USD" in text


def test_names_are_escaped():
    text = render_debt_reminder("en", reminder(ReminderKind.TODAY, -1, name="<b>x</b>"))
    assert "&lt;b&gt;x&lt;/b&gt;" in text


@pytest.mark.parametrize("lang", ["ru", "uz"])
@pytest.mark.parametrize("kind", list(ReminderKind))
@pytest.mark.parametrize("balance", [-1_000, 1_000])
def test_every_combination_exists_in_every_language(lang, kind, balance):
    text = render_debt_reminder(lang, reminder(kind, balance))
    assert "Aziz" in text and "1 000 UZS" in text


def test_evening_reminder_with_and_without_a_total():
    plain = render_evening("en", EveningReminder(1, 1, "en", date(2026, 11, 17), {}))
    assert "Evening check-in" in plain and "Spent today" not in plain
    with_total = render_evening("en", EveningReminder(1, 1, "en", date(2026, 11, 17), {"UZS": 45_000, "USD": 500}))
    assert "Spent today: <b>5 USD, 45 000 UZS</b>" in with_total
