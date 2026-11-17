"""Parser tests. Amounts are in minor units (UZS: sums, USD/EUR/RUB: cents)."""
from dataclasses import FrozenInstanceError

import pytest

from app.core.parser import (
    MAX_CANDIDATES,
    EntryType,
    ParseError,
    ParseResult,
    is_large_amount,
    parse_amount,
)

E, I = "expense", "income"

VALID = [
    # --- thousands separators and plain numbers: text, amount, currency, type, note
    ("10000", 10000, "UZS", E, None),
    ("10.000", 10000, "UZS", E, None),
    ("12 500", 12500, "UZS", E, None),
    ("1,500,000", 1500000, "UZS", E, None),
    ("1 500 000", 1500000, "UZS", E, None),
    ("1.500", 1500, "UZS", E, None),
    ("10\u00a0000", 10000, "UZS", E, None),  # non-breaking space from copy-paste
    # --- suffixes
    ("10k", 10000, "UZS", E, None),
    ("10\u043a", 10000, "UZS", E, None),  # Cyrillic "\u043a"
    ("10 K", 10000, "UZS", E, None),
    ("1.5k", 1500, "UZS", E, None),
    ("10,5k", 10500, "UZS", E, None),
    ("1.5 mln", 1500000, "UZS", E, None),
    ("1.5 \u043c\u043b\u043d", 1500000, "UZS", E, None),
    ("2m", 2000000, "UZS", E, None),
    ("1,5m", 1500000, "UZS", E, None),
    ("1.500 mln", 1500000, "UZS", E, None),  # with a suffix the dot is decimal
    ("5 m", 5, "UZS", E, "m"),  # a lone "m" must touch the number
    # --- income
    ("+2000000", 2000000, "UZS", I, None),
    ("+ 2000000 salary", 2000000, "UZS", I, "salary"),
    ("bread +5000", 5000, "UZS", I, "bread"),
    ("+$50 gift", 5000, "USD", I, "gift"),
    # --- notes
    ("bread 10000", 10000, "UZS", E, "bread"),
    ("10000 bread", 10000, "UZS", E, "bread"),
    ("10 000 fresh bread", 10000, "UZS", E, "fresh bread"),
    ("bread, 10000", 10000, "UZS", E, "bread"),
    ("bread,10000", 10000, "UZS", E, "bread"),
    ("\u043e\u0431\u0435\u0434 25000", 25000, "UZS", E, "\u043e\u0431\u0435\u0434"),
    ("10000 bread 2.5 kg", 10000, "UZS", E, "bread 2.5 kg"),  # 2.5 is not a valid UZS amount
    # --- other currencies
    ("$50", 5000, "USD", E, None),
    ("50$", 5000, "USD", E, None),
    ("50 usd", 5000, "USD", E, None),
    ("50USD", 5000, "USD", E, None),
    ("usd 50", 5000, "USD", E, None),
    ("50.50 usd", 5050, "USD", E, None),
    ("0.5 usd", 50, "USD", E, None),
    ("0.500 usd", 50, "USD", E, None),
    ("1,500.50 usd", 150050, "USD", E, None),
    ("1.500,50 usd", 150050, "USD", E, None),
    ("\u20ac20", 2000, "EUR", E, None),
    ("20 eur", 2000, "EUR", E, None),
    ("500 \u0440\u0443\u0431", 50000, "RUB", E, None),
    ("\u20bd500", 50000, "RUB", E, None),
    ("1.5 mln usd", 150000000, "USD", E, None),
    ("10k usd lunch", 1000000, "USD", E, "lunch"),
    ("50 000 \u0441\u0443\u043c", 50000, "UZS", E, None),
    ("10000 so'm", 10000, "UZS", E, None),
    ("10000 so\u2018m", 10000, "UZS", E, None),  # curly apostrophe
    ("10 000 UZS lunch", 10000, "UZS", E, "lunch"),
    # --- the same amount twice is one amount
    ("10000 10000", 10000, "UZS", E, None),
    ("10k and 10000", 10000, "UZS", E, "and"),
]


@pytest.mark.parametrize("text,amount,currency,entry_type,note", VALID)
def test_valid_input(text, amount, currency, entry_type, note):
    result = parse_amount(text)
    assert result.error is None, f"{text!r} -> {result.error}"
    assert (result.amount, result.currency, result.type, result.note) == (
        amount,
        currency,
        entry_type,
        note,
    )


ERRORS = [
    ("", ParseError.NO_AMOUNT),
    ("   ", ParseError.NO_AMOUNT),
    (None, ParseError.NO_AMOUNT),
    ("hello bread", ParseError.NO_AMOUNT),
    ("+", ParseError.NO_AMOUNT),
    ("\U0001F35E\U0001F35E", ParseError.NO_AMOUNT),
    ("k", ParseError.NO_AMOUNT),
    ("0", ParseError.ZERO_AMOUNT),
    ("0 usd", ParseError.ZERO_AMOUNT),
    ("0.5", ParseError.TOO_MANY_DECIMALS),  # UZS has no minor units
    ("100.5", ParseError.TOO_MANY_DECIMALS),
    ("10.000.5", ParseError.INVALID_AMOUNT),
    ("$50 eur", ParseError.INVALID_AMOUNT),  # two different currencies
    ("10000000000000", ParseError.TOO_LARGE),
    ("2000000 mln", ParseError.TOO_LARGE),
    ("9" * 40, ParseError.TOO_LARGE),
]


@pytest.mark.parametrize("text,error", ERRORS)
def test_errors(text, error):
    result = parse_amount(text)
    assert result.error is error
    assert result.amount is None
    assert result.ok is False


def test_multiple_different_amounts_return_candidates():
    result = parse_amount("10000 20000")
    assert result.error is ParseError.MULTIPLE_AMOUNTS
    assert result.amount is None
    assert [(c.amount, c.currency) for c in result.candidates] == [
        (10000, "UZS"),
        (20000, "UZS"),
    ]


def test_candidates_carry_their_own_note():
    result = parse_amount("2 kg bread 10000")
    assert result.error is ParseError.MULTIPLE_AMOUNTS
    by_amount = {c.amount: c.note for c in result.candidates}
    assert by_amount == {2: "kg bread 10000", 10000: "2 kg bread"}


def test_candidates_keep_their_own_currency():
    result = parse_amount("50 usd 10000")
    assert [(c.amount, c.currency) for c in result.candidates] == [
        (5000, "USD"),
        (10000, "UZS"),
    ]


def test_candidates_are_capped():
    result = parse_amount("1 2 3 4 5 6 7 8 9")
    assert result.error is ParseError.MULTIPLE_AMOUNTS
    assert len(result.candidates) == MAX_CANDIDATES


def test_income_flag_survives_an_error():
    result = parse_amount("+ 10000 20000")
    assert result.type == EntryType.INCOME
    assert result.error is ParseError.MULTIPLE_AMOUNTS


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1000000000", False),  # exactly 1 billion is fine
        ("1000 mln", False),
        ("1000000001", True),
        ("1001 mln", True),
        ("5000000000", True),
        ("10000", False),
    ],
)
def test_large_amounts_need_confirmation(text, expected):
    result = parse_amount(text)
    assert result.error is None
    assert result.needs_confirmation is expected


def test_default_currency_is_used_when_none_is_written():
    result = parse_amount("50", default_currency="USD")
    assert (result.amount, result.currency) == (5000, "USD")


def test_written_currency_beats_the_default():
    result = parse_amount("50 uzs", default_currency="USD")
    assert (result.amount, result.currency) == (50, "UZS")


def test_unsupported_default_currency_is_a_programming_error():
    with pytest.raises(ValueError):
        parse_amount("50", default_currency="XYZ")


def test_result_is_immutable_and_has_an_ok_flag():
    result = parse_amount("10k")
    assert isinstance(result, ParseResult)
    assert result.ok is True
    with pytest.raises(FrozenInstanceError):
        result.amount = 1


@pytest.mark.parametrize(
    "text",
    [
        "\x00",
        "\U0001F4A5" * 1000,
        "9" * 5000,
        "1" + "." * 200,
        ". , . ,",
        "1 " * 500,
        "$" * 50,
        "+++",
        "1e10",
        "-",
        "\n\n10000\n\nbread\n",
        "\u0663\u0660\u0660",  # Arabic-Indic digits
        "x" * 10000 + " 5000",
    ],
)
def test_weird_input_never_raises(text):
    result = parse_amount(text)
    assert isinstance(result, ParseResult)
    assert (result.amount is None) == (result.error is not None)


@pytest.mark.parametrize(
    "amount,currency,expected",
    [
        (1_000_000_000, "UZS", False),
        (1_000_000_001, "UZS", True),
        (100_000_000_000, "USD", False),  # 1 billion dollars, counted in cents
        (100_000_000_001, "USD", True),
    ],
)
def test_is_large_amount_for_candidates(amount, currency, expected):
    assert is_large_amount(amount, currency) is expected
