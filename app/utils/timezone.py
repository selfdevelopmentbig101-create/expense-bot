"""Time zone helpers. The database stores UTC; users see their own time zone."""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "Asia/Tashkent"


def get_zone(name: str | None) -> ZoneInfo:
    """Return the zone, falling back to Asia/Tashkent for a missing or broken name."""
    try:
        return ZoneInfo(name or DEFAULT_TIMEZONE)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        return ZoneInfo(DEFAULT_TIMEZONE)


def local_day_bounds(now_utc: datetime, tz_name: str | None) -> tuple[datetime, datetime]:
    """[start, end) of the user's current local day, as UTC datetimes."""
    zone = get_zone(tz_name)
    local_date = now_utc.astimezone(zone).date()
    start = datetime.combine(local_date, time.min, tzinfo=zone)
    end = datetime.combine(local_date + timedelta(days=1), time.min, tzinfo=zone)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def to_local(dt_utc: datetime, tz_name: str | None) -> datetime:
    return dt_utc.astimezone(get_zone(tz_name))


def format_date(dt_utc: datetime, tz_name: str | None) -> str:
    return to_local(dt_utc, tz_name).strftime("%d.%m.%Y")


def format_time(dt_utc: datetime, tz_name: str | None) -> str:
    return to_local(dt_utc, tz_name).strftime("%H:%M")


def _bounds(zone: ZoneInfo, first_day: date, day_after_last: date) -> tuple[datetime, datetime]:
    start = datetime.combine(first_day, time.min, tzinfo=zone)
    end = datetime.combine(day_after_last, time.min, tzinfo=zone)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def local_week_bounds(now_utc: datetime, tz_name: str | None) -> tuple[datetime, datetime]:
    """[start, end) of the current calendar week (Monday to Sunday), as UTC."""
    zone = get_zone(tz_name)
    today = now_utc.astimezone(zone).date()
    monday = today - timedelta(days=today.weekday())
    return _bounds(zone, monday, monday + timedelta(days=7))


def local_month_bounds(now_utc: datetime, tz_name: str | None) -> tuple[datetime, datetime]:
    """[start, end) of the current calendar month, as UTC."""
    zone = get_zone(tz_name)
    today = now_utc.astimezone(zone).date()
    first = today.replace(day=1)
    next_first = date(first.year + (first.month == 12), first.month % 12 + 1, 1)
    return _bounds(zone, first, next_first)


def local_dates(start_utc: datetime, end_utc: datetime, tz_name: str | None) -> tuple[date, date]:
    """First and last LOCAL day of a [start, end) range (for labels)."""
    zone = get_zone(tz_name)
    first = start_utc.astimezone(zone).date()
    last = (end_utc - timedelta(microseconds=1)).astimezone(zone).date()
    return first, last


def format_short(dt_utc: datetime, tz_name: str | None) -> str:
    """17.11 19:05"""
    return to_local(dt_utc, tz_name).strftime("%d.%m %H:%M")
