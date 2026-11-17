"""The parser must survive anything a user (or a cat on the keyboard) can type."""
import random
import time

import pytest

from app.core.parser import ParseError, ParseResult, parse_amount


def test_a_message_of_the_maximum_length_is_parsed_quickly():
    text = "bread 10000 " + "word " * 190  # about 1000 characters
    started = time.perf_counter()
    result = parse_amount(text)
    assert time.perf_counter() - started < 1.0
    assert result.amount == 10_000


def test_pathological_inputs_do_not_blow_up():
    started = time.perf_counter()
    for text in ("1 " * 500, "1." * 500, "1," * 500, "9" * 4000, "1" + " 000" * 300, "\u20ac" * 500, "k " * 500, "+ " * 500):
        result = parse_amount(text)
        assert isinstance(result, ParseResult)
    assert time.perf_counter() - started < 3.0


@pytest.mark.parametrize(
    "text,amount",
    [
        ("\uff11\uff10\uff10\uff10\uff10", 10_000),  # full-width digits
        ("\U0001F4B0 10000", 10_000),  # an emoji in front
        ("10000\u200b", 10_000),  # a zero-width space at the end
        ("\u200f10000", 10_000),  # a right-to-left mark
        ("10000\r\nbread", 10_000),  # a Windows line break
        ("\t10000\t", 10_000),
    ],
)
def test_odd_but_readable_input(text, amount):
    result = parse_amount(text)
    assert result.error is None and result.amount == amount


def test_random_garbage_never_raises_and_always_gives_a_consistent_result():
    rng = random.Random(20261117)
    alphabet = list("0123456789") * 4 + list(" .,+-$\u20ac\u20bdkm\u043a\u043c\u043b\u043d\u0440\u0443\u0431usdeurmlnso'\u2018\n\t") + list("abc\U0001F4B0\u0663")
    for _ in range(3000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40)))
        result = parse_amount(text)
        assert isinstance(result, ParseResult), text
        if result.error is None:
            assert isinstance(result.amount, int) and 0 < result.amount < 10**15, text
        else:
            assert result.amount is None, text
            assert isinstance(result.error, ParseError)
        if result.error is ParseError.MULTIPLE_AMOUNTS:
            assert 2 <= len(result.candidates) <= 5, text
