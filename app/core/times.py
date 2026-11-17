"""Time-of-day parsing for the reminder setting. Pure logic."""
import re
from datetime import time

_TIME_RE = re.compile(r"^\s*(\d{1,2})[:.](\d{2})\s*$")


def parse_hhmm(text: str) -> time | None:
    """"21:30", "9:05" and "21.30" -> time. None when it is not a real time."""
    match = _TIME_RE.match(text or "")
    if not match:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        return None
    return time(hour, minute)


def format_hhmm(value: time) -> str:
    return value.strftime("%H:%M")
