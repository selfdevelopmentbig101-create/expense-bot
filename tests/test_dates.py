from datetime import date

import pytest

from app.core.dates import add_months, due_from_choice, format_user_date, parse_user_date


@pytest.mark.parametrize(
    "start,months,expected",
    [
        (date(2026, 11, 17), 1, date(2026, 12, 17)),
        (date(2026, 12, 17), 1, date(2027, 1, 17)),  # year rollover
        (date(2026, 1, 31), 1, date(2026, 2, 28)),  # day is clamped
        (date(2028, 1, 31), 1, date(2028, 2, 29)),  # leap year
        (date(2026, 3, 31), 1, date(2026, 4, 30)),
    ],
)
def test_add_months(start, months, expected):
    assert add_months(start, months) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("25.11.2026", date(2026, 11, 25)),
        (" 25.11.2026 ", date(2026, 11, 25)),
        ("5.1.2027", date(2027, 1, 5)),
        ("25/11/2026", date(2026, 11, 25)),
        ("25-11-2026", date(2026, 11, 25)),
        ("29.02.2028", date(2028, 2, 29)),
    ],
)
def test_parse_valid_dates(text, expected):
    assert parse_user_date(text) == expected


@pytest.mark.parametrize(
    "text",
    ["", "tomorrow", "31.02.2026", "29.02.2027", "32.01.2026", "25.13.2026", "25.11.26", "2026-11-25", "25.11"],
)
def test_parse_invalid_dates(text):
    assert parse_user_date(text) is None


def test_due_from_choice():
    today = date(2026, 11, 17)
    assert due_from_choice("none", today) is None
    assert due_from_choice("w1", today) == date(2026, 11, 24)
    assert due_from_choice("m1", today) == date(2026, 12, 17)
    with pytest.raises(ValueError):
        due_from_choice("pick", today)


def test_format_user_date():
    assert format_user_date(date(2026, 11, 5)) == "05.11.2026"
