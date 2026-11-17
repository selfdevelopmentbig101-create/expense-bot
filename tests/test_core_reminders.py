from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from app.core.reminders import ReminderKind, evening_due, reminder_kind

DUE = date(2026, 11, 25)
T, TD, OD = ReminderKind.TOMORROW, ReminderKind.TODAY, ReminderKind.OVERDUE


@pytest.mark.parametrize(
    "today,last,snooze,expected",
    [
        (date(2026, 11, 22), None, None, None),  # 3 days before: too early
        (date(2026, 11, 23), None, None, None),  # 2 days before
        (date(2026, 11, 24), None, None, T),  # the day before
        (date(2026, 11, 25), None, None, TD),  # the due date
        (date(2026, 11, 25), date(2026, 11, 24), None, TD),  # "tomorrow" was sent yesterday
        (date(2026, 11, 26), None, None, OD),  # never reminded: now overdue
        (date(2026, 11, 26), date(2026, 11, 25), None, None),  # reminded yesterday
        (date(2026, 11, 27), date(2026, 11, 25), None, None),  # 2 days since the last one
        (date(2026, 11, 28), date(2026, 11, 25), None, OD),  # every 3 days
        (date(2026, 12, 1), date(2026, 11, 28), None, OD),
        (date(2026, 11, 29), date(2026, 11, 28), None, None),
    ],
)
def test_reminder_schedule(today, last, snooze, expected):
    assert reminder_kind(today, DUE, last, snooze) is expected


def test_never_twice_on_the_same_day():
    for today in (date(2026, 11, 24), date(2026, 11, 25), date(2026, 12, 3)):
        assert reminder_kind(today, DUE, today, None) is None


def test_postponed_debts_stay_quiet_until_the_snooze_ends():
    last = date(2026, 11, 28)
    snooze = date(2026, 12, 5)
    assert reminder_kind(date(2026, 12, 4), DUE, last, snooze) is None
    assert reminder_kind(date(2026, 12, 5), DUE, last, snooze) is OD  # 7 days since the last one


def test_ignore_history_is_for_manual_tests():
    today = date(2026, 11, 25)
    assert reminder_kind(today, DUE, today, date(2026, 12, 31)) is None
    assert reminder_kind(today, DUE, today, date(2026, 12, 31), ignore_history=True) is TD
    assert reminder_kind(date(2026, 11, 26), DUE, date(2026, 11, 26), None, ignore_history=True) is OD
    assert reminder_kind(date(2026, 11, 20), DUE, None, None, ignore_history=True) is None  # still too early


TZ = ZoneInfo("Asia/Tashkent")


def local(hour, minute=0, day=17):
    return datetime(2026, 11, day, hour, minute, tzinfo=TZ)


@pytest.mark.parametrize(
    "now,expected",
    [
        (local(20, 59), False),
        (local(21, 0), True),
        (local(21, 1), True),
        (local(23, 59), True),
        (local(0, 30, day=18), False),  # a new day: the old window is over
        (local(8, 0), False),
    ],
)
def test_evening_reminder_window(now, expected):
    assert evening_due(now, time(21, 0), None) is expected


def test_evening_window_is_three_hours_so_a_restart_does_not_send_a_stale_reminder():
    assert evening_due(local(21, 59), time(19, 0), None) is True
    assert evening_due(local(22, 0), time(19, 0), None) is False


def test_evening_is_sent_once_per_day_and_only_when_switched_on():
    assert evening_due(local(21, 5), time(21, 0), date(2026, 11, 17)) is False
    assert evening_due(local(21, 5), time(21, 0), date(2026, 11, 16)) is True
    assert evening_due(local(21, 5), None, None) is False
