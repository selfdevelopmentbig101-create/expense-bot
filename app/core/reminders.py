"""When is a reminder due? Pure logic."""
from datetime import date, datetime, time, timedelta
from enum import StrEnum

POSTPONE_DAYS = 7
OVERDUE_EVERY_DAYS = 3
EVENING_WINDOW = timedelta(hours=3)  # do not send a stale reminder after a long downtime


class ReminderKind(StrEnum):
    TOMORROW = "tomorrow"
    TODAY = "today"
    OVERDUE = "overdue"


def reminder_kind(
    today: date,
    due: date,
    last_reminded_on: date | None,
    snoozed_until: date | None,
    *,
    ignore_history: bool = False,
) -> ReminderKind | None:
    """Which reminder (if any) a debt with this due date gets today.

    * one day before the due date, and on the due date (once each);
    * after the due date: a gentle reminder every 3 days;
    * never twice on the same day, and never while snoozed.
    ignore_history is for manual tests: it skips the "already reminded" checks.
    """
    if not ignore_history:
        if snoozed_until is not None and today < snoozed_until:
            return None
        if last_reminded_on == today:
            return None

    if today == due - timedelta(days=1):
        return ReminderKind.TOMORROW
    if today == due:
        return ReminderKind.TODAY
    if today > due:
        never = last_reminded_on is None
        if ignore_history or never or (today - last_reminded_on).days >= OVERDUE_EVERY_DAYS:
            return ReminderKind.OVERDUE
    return None


def evening_due(
    local_now: datetime, reminder_time: time | None, last_sent_on: date | None
) -> bool:
    """True from the chosen time until 3 hours later, once per local day."""
    if reminder_time is None or last_sent_on == local_now.date():
        return False
    scheduled = datetime.combine(local_now.date(), reminder_time, tzinfo=local_now.tzinfo)
    return timedelta(0) <= local_now - scheduled < EVENING_WINDOW
