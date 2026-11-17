import pytest

from app.core.times import format_hhmm, parse_hhmm
from datetime import time


@pytest.mark.parametrize(
    "text,expected",
    [
        ("21:30", time(21, 30)),
        (" 9:05 ", time(9, 5)),
        ("21.30", time(21, 30)),
        ("00:00", time(0, 0)),
        ("23:59", time(23, 59)),
    ],
)
def test_valid_times(text, expected):
    assert parse_hhmm(text) == expected


@pytest.mark.parametrize("text", ["", "24:00", "12:60", "9", "9:5", "abc", "21:30:00", "-1:00", None])
def test_invalid_times(text):
    assert parse_hhmm(text) is None


def test_format():
    assert format_hhmm(time(9, 5)) == "09:05"
