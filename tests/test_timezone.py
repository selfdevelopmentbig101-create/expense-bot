from datetime import datetime, timezone

from app.utils.timezone import format_date, format_time, get_zone, local_day_bounds

UTC = timezone.utc


def utc(*args):
    return datetime(*args, tzinfo=UTC)


def test_day_bounds_in_tashkent():
    # 17:00 in Tashkent on 17 Nov -> the day started at 00:00 +05 = 19:00 UTC on the 16th
    start, end = local_day_bounds(utc(2026, 11, 17, 12, 0), "Asia/Tashkent")
    assert start == utc(2026, 11, 16, 19, 0)
    assert end == utc(2026, 11, 17, 19, 0)


def test_after_local_midnight_is_the_next_day():
    # 20:30 UTC = 01:30 on the 18th in Tashkent
    start, end = local_day_bounds(utc(2026, 11, 17, 20, 30), "Asia/Tashkent")
    assert start == utc(2026, 11, 17, 19, 0)
    assert end == utc(2026, 11, 18, 19, 0)


def test_just_before_local_midnight_is_still_today():
    start, _ = local_day_bounds(utc(2026, 11, 17, 18, 59), "Asia/Tashkent")
    assert start == utc(2026, 11, 16, 19, 0)


def test_another_zone():
    start, end = local_day_bounds(utc(2026, 11, 17, 12, 0), "UTC")
    assert (start, end) == (utc(2026, 11, 17, 0, 0), utc(2026, 11, 18, 0, 0))


def test_broken_zone_name_falls_back_to_tashkent():
    assert get_zone("Mars/Base").key == "Asia/Tashkent"
    assert get_zone("").key == "Asia/Tashkent"
    assert get_zone(None).key == "Asia/Tashkent"


def test_display_format():
    moment = utc(2026, 11, 17, 14, 5)
    assert format_date(moment, "Asia/Tashkent") == "17.11.2026"
    assert format_time(moment, "Asia/Tashkent") == "19:05"
    assert format_date(utc(2026, 11, 17, 20, 30), "Asia/Tashkent") == "18.11.2026"
