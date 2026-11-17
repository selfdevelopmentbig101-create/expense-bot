from datetime import date, datetime, timezone

from app.utils.timezone import format_short, local_dates, local_month_bounds, local_week_bounds


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


TZ = "Asia/Tashkent"


def test_week_runs_monday_to_sunday():
    # Tuesday 17 Nov 2026 -> Monday 16 Nov 00:00 +05 .. Monday 23 Nov 00:00 +05
    start, end = local_week_bounds(utc(2026, 11, 17, 12, 0), TZ)
    assert start == utc(2026, 11, 15, 19, 0)
    assert end == utc(2026, 11, 22, 19, 0)
    assert local_dates(start, end, TZ) == (date(2026, 11, 16), date(2026, 11, 22))


def test_the_week_changes_at_local_midnight_not_at_utc_midnight():
    last_minute = local_week_bounds(utc(2026, 11, 22, 18, 59), TZ)  # Sunday 23:59 local
    first_minute = local_week_bounds(utc(2026, 11, 22, 19, 0), TZ)  # Monday 00:00 local
    assert last_minute[0] == utc(2026, 11, 15, 19, 0)
    assert first_minute[0] == utc(2026, 11, 22, 19, 0)


def test_a_monday_belongs_to_its_own_week():
    start, _ = local_week_bounds(utc(2026, 11, 16, 1, 0), TZ)
    assert start == utc(2026, 11, 15, 19, 0)


def test_month_bounds():
    start, end = local_month_bounds(utc(2026, 11, 17, 12, 0), TZ)
    assert start == utc(2026, 10, 31, 19, 0)
    assert end == utc(2026, 11, 30, 19, 0)
    assert local_dates(start, end, TZ) == (date(2026, 11, 1), date(2026, 11, 30))


def test_december_rolls_over_to_january():
    start, end = local_month_bounds(utc(2026, 12, 15, 12, 0), TZ)
    assert start == utc(2026, 11, 30, 19, 0)
    assert end == utc(2026, 12, 31, 19, 0)
    assert local_dates(start, end, TZ) == (date(2026, 12, 1), date(2026, 12, 31))


def test_february_in_a_leap_year():
    start, end = local_month_bounds(utc(2028, 2, 10, 12, 0), TZ)
    assert local_dates(start, end, TZ) == (date(2028, 2, 1), date(2028, 2, 29))


def test_format_short():
    assert format_short(utc(2026, 11, 17, 14, 5), TZ) == "17.11 19:05"
