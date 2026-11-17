"""Date helpers for due dates. Pure logic."""
import re
from calendar import monthrange
from datetime import date, timedelta

_DATE_RE = re.compile(r"^\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})\s*$")


def add_months(day: date, months: int) -> date:
    """31 Jan + 1 month = 28/29 Feb (the day is clamped, never overflows)."""
    index = day.year * 12 + (day.month - 1) + months
    year, month = divmod(index, 12)
    month += 1
    return date(year, month, min(day.day, monthrange(year, month)[1]))


def parse_user_date(text: str) -> date | None:
    """DD.MM.YYYY (also / or - as separator). None when it is not a real date."""
    match = _DATE_RE.match(text or "")
    if not match:
        return None
    day, month, year = (int(part) for part in match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


def format_user_date(day: date) -> str:
    return day.strftime("%d.%m.%Y")


def due_from_choice(choice: str, today: date) -> date | None:
    """Buttons: none = no deadline, w1 = in 1 week, m1 = in 1 month."""
    if choice == "none":
        return None
    if choice == "w1":
        return today + timedelta(days=7)
    if choice == "m1":
        return add_months(today, 1)
    raise ValueError(f"Unknown due date choice: {choice}")
