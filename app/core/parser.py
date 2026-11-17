"""Amount parser: turns a chat message into a ParseResult.

Pure logic. No Telegram, no database, no I/O.

Rules
-----
* A leading "+" means income. A "+" glued to the amount also does ("bread +5000").
* A dot, comma or space followed by EXACTLY 3 digits is a thousands separator:
  "10.000" = 10000, "12 500" = 12500, "1,500,000" = 1500000, "1.500" = 1500.
* Any other dot or comma is a decimal point: "1.5" = 1.5, "50.50 usd" = 50.50.
* With a suffix (k, mln ...) a single dot or comma is always a decimal point:
  "1.5 mln" = 1 500 000 and "1.500 mln" = 1 500 000 too.
* Suffixes: k, к (x1 000); mln, млн, m (x1 000 000). "m" must touch the number
  ("1.5m"); the others may be separated by one space ("1.5 mln", "10 k").
* Currency: UZS by default. Also usd/$, eur/€, rub/руб/₽, uzs/сум/so'm ...,
  before or after the amount ("$50", "50 usd", "usd 50").
* Several different amounts: error MULTIPLE_AMOUNTS plus the candidates, so the
  bot can ask which one to use. The same amount written twice counts as one.
* The amount is returned in MINOR units (UZS: 1 = 1 sum, USD: 1 = 1 cent).
* More than LARGE_AMOUNT_MAJOR (1 billion) sets needs_confirmation.
"""
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, localcontext
from enum import StrEnum

from app.core.money import CURRENCY_EXPONENTS, DEFAULT_CURRENCY

LARGE_AMOUNT_MAJOR = 1_000_000_000  # above this the user must confirm
MAX_AMOUNT_MAJOR = 1_000_000_000_000  # above this the input is rejected
MAX_INT_DIGITS = 18
MAX_DECIMAL_DIGITS = 18
MAX_CANDIDATES = 5


class EntryType(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"


class ParseError(StrEnum):
    NO_AMOUNT = "no_amount"  # nothing that looks like a number
    INVALID_AMOUNT = "invalid_amount"  # digits are there but make no sense
    MULTIPLE_AMOUNTS = "multiple_amounts"  # ask the user which one
    ZERO_AMOUNT = "zero_amount"
    TOO_MANY_DECIMALS = "too_many_decimals"  # e.g. 0.5 UZS (no minor units)
    TOO_LARGE = "too_large"


@dataclass(frozen=True, slots=True)
class Candidate:
    """One possible reading when the message holds several amounts."""

    amount: int  # minor units
    currency: str
    note: str | None  # the message without this amount


@dataclass(frozen=True, slots=True)
class ParseResult:
    amount: int | None = None  # minor units; None when there is an error
    currency: str = DEFAULT_CURRENCY
    type: EntryType = EntryType.EXPENSE
    note: str | None = None
    error: ParseError | None = None
    needs_confirmation: bool = False  # amount above 1 billion
    candidates: tuple[Candidate, ...] = ()  # only with MULTIPLE_AMOUNTS

    @property
    def ok(self) -> bool:
        return self.error is None


# --------------------------------------------------------------------------- #
# Currency words and symbols
# --------------------------------------------------------------------------- #
# Every apostrophe people type in so'm: ' \u2018 \u2019 \u02bb \u02bc `
_APOS = "['\u2018\u2019\u02bb\u02bc`]"

_WORD_TO_CODE = {
    "uzs": "UZS", "sum": "UZS", "som": "UZS", "soum": "UZS", "so'm": "UZS",
    "сум": "UZS", "сумов": "UZS", "сўм": "UZS",
    "usd": "USD", "dollar": "USD", "dollars": "USD",
    "доллар": "USD", "доллара": "USD", "долларов": "USD", "долл": "USD",
    "eur": "EUR", "euro": "EUR", "евро": "EUR",
    "rub": "RUB", "руб": "RUB", "рубль": "RUB", "рубля": "RUB", "рублей": "RUB",
}
_SYMBOL_TO_CODE = {"$": "USD", "€": "EUR", "₽": "RUB"}

_NOT_LETTER_AFTER = r"(?![^\W\d_])"
_NOT_LETTER_BEFORE = r"(?<![^\W\d_])"
_WORD_ALT = "|".join(
    re.escape(word).replace("'", _APOS) for word in sorted(_WORD_TO_CODE, key=len, reverse=True)
)
_CUR_AFTER = re.compile(
    rf" ?(?:(?P<w>{_WORD_ALT}){_NOT_LETTER_AFTER}|(?P<s>[$€₽]))", re.IGNORECASE
)
_CUR_BEFORE = re.compile(
    rf"(?:{_NOT_LETTER_BEFORE}(?P<w>{_WORD_ALT})|(?P<s>[$€₽])) ?$", re.IGNORECASE
)

# --------------------------------------------------------------------------- #
# Numbers and suffixes
# --------------------------------------------------------------------------- #
_NUMBER_RE = re.compile(
    r"""
    (?<!\d)(?<!\d[.,])                      # not in the middle of another number
    (?P<int>\d{1,3}(?:[ .,]\d{3})+|\d+)     # grouped (10.000) or plain (10000)
    (?:(?P<dsep>[.,])(?P<dec>\d+))?         # optional decimal part
    (?!\d)
    """,
    re.VERBOSE,
)
# k and к may follow after one space; mln and млн too; a lone m must touch the number
_MULT_RE = re.compile(
    r"(?: ?(?P<big>mln|млн)\.?| ?(?P<k>k|к)|(?P<m>m))" + _NOT_LETTER_AFTER,
    re.IGNORECASE,
)
_DIGIT_RE = re.compile(r"\d")


class _Fail(Exception):
    def __init__(self, error: ParseError) -> None:
        super().__init__(error)
        self.error = error


@dataclass(frozen=True, slots=True)
class _Hit:
    start: int  # span in the text, including a prefix currency and a glued "+"
    end: int
    amount: int  # minor units
    currency: str
    plus: bool
    major: Decimal  # value in major units (for the 1 billion check)


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)  # NBSP, thin spaces, full-width digits
    text = re.sub("[\u200b-\u200d\ufeff]", "", text)  # zero-width characters
    return text.strip()


def _currency_of(match: re.Match) -> str:
    word = match.group("w")
    if word is not None:
        return _WORD_TO_CODE[re.sub(_APOS, "'", word.lower())]
    return _SYMBOL_TO_CODE[match.group("s")]


def _interpret(int_part: str, dsep: str | None, dec: str | None, has_multiplier: bool) -> Decimal:
    """Apply the separator rules to the digits of one number."""
    separators = re.findall(r"[ .,]", int_part)
    if separators:
        if len(set(separators)) != 1:
            raise _Fail(ParseError.INVALID_AMOUNT)
        sep = separators[0]
        if dsep == sep:  # "10.000.5": the same sign cannot be both
            raise _Fail(ParseError.INVALID_AMOUNT)
        single = len(separators) == 1
        leading_zero = int_part.startswith("0")
        if single and sep in ".," and dec is None and (has_multiplier or leading_zero):
            return Decimal(int_part.replace(sep, "."))  # "1.5 mln", "0.500"
        if leading_zero:
            raise _Fail(ParseError.INVALID_AMOUNT)
        digits = int_part.replace(sep, "")
    else:
        digits = int_part

    if len(digits) > MAX_INT_DIGITS:
        raise _Fail(ParseError.TOO_LARGE)
    if dec is not None:
        if len(dec) > MAX_DECIMAL_DIGITS:
            raise _Fail(ParseError.TOO_MANY_DECIMALS)
        return Decimal(f"{digits}.{dec}")
    return Decimal(digits)


def _resolve(body: str, match: re.Match, default_currency: str, floor: int) -> _Hit:
    """Read the suffix, currency and sign around one number. Raises _Fail."""
    number_start, pos = match.start(), match.end()

    multiplier = 1
    mult = _MULT_RE.match(body, pos)
    if mult:
        multiplier = 1_000 if mult.group("k") else 1_000_000
        pos = mult.end()

    suffix_currency = None
    after = _CUR_AFTER.match(body, pos)
    if after:
        suffix_currency = _currency_of(after)
        pos = after.end()

    start, prefix_currency = number_start, None
    before = _CUR_BEFORE.search(body, floor, number_start)
    if before:
        prefix_currency = _currency_of(before)
        start = before.start()

    if prefix_currency and suffix_currency and prefix_currency != suffix_currency:
        raise _Fail(ParseError.INVALID_AMOUNT)  # "$50 eur"
    currency = suffix_currency or prefix_currency or default_currency

    plus = False
    if start > 0 and body[start - 1] == "+" and (start == 1 or body[start - 2].isspace()):
        plus, start = True, start - 1

    with localcontext() as ctx:
        ctx.prec = 80
        number = _interpret(
            match.group("int"), match.group("dsep"), match.group("dec"), multiplier != 1
        )
        major = number * multiplier
        if major <= 0:
            raise _Fail(ParseError.ZERO_AMOUNT)
        if major > MAX_AMOUNT_MAJOR:
            raise _Fail(ParseError.TOO_LARGE)
        minor = major.scaleb(CURRENCY_EXPONENTS[currency])
        if minor != minor.to_integral_value():
            raise _Fail(ParseError.TOO_MANY_DECIMALS)
        amount = int(minor)

    return _Hit(start, pos, amount, currency, plus, major)


def _make_note(body: str, spans: list[tuple[int, int]]) -> str | None:
    """The message without the amount spans, tidied up."""
    parts, pos = [], 0
    for start, end in sorted(spans):
        parts.append(body[pos:start])
        pos = max(pos, end)
    parts.append(body[pos:])
    note = re.sub(r"\s+", " ", " ".join(parts)).strip(" ,.;:-\u2013\u2014")
    return note or None


def parse_amount(text: str | None, default_currency: str = DEFAULT_CURRENCY) -> ParseResult:
    """Parse one chat message. Never raises on user input."""
    if default_currency not in CURRENCY_EXPONENTS:
        raise ValueError(f"Unsupported default currency: {default_currency}")

    body = _normalize(text)
    income = body.startswith("+")
    if income:
        body = body[1:]

    def failure(error: ParseError, **extra) -> ParseResult:
        entry_type = EntryType.INCOME if income else EntryType.EXPENSE
        return ParseResult(currency=default_currency, type=entry_type, error=error, **extra)

    matches = list(_NUMBER_RE.finditer(body))
    if not matches:
        has_digits = _DIGIT_RE.search(body) is not None
        return failure(ParseError.INVALID_AMOUNT if has_digits else ParseError.NO_AMOUNT)

    hits: list[_Hit] = []
    first_error: ParseError | None = None
    floor = 0
    for match in matches:
        try:
            hit = _resolve(body, match, default_currency, floor)
        except _Fail as exc:
            first_error = first_error or exc.error
            continue
        hits.append(hit)
        floor = hit.end
    if not hits:
        return failure(first_error or ParseError.INVALID_AMOUNT)

    income = income or any(hit.plus for hit in hits)
    entry_type = EntryType.INCOME if income else EntryType.EXPENSE

    # Group identical readings: "10k and 10000" is one amount, not two.
    groups: dict[tuple[int, str], list[_Hit]] = {}
    for hit in hits:
        groups.setdefault((hit.amount, hit.currency), []).append(hit)

    if len(groups) > 1:
        candidates = tuple(
            Candidate(amount, currency, _make_note(body, [(h.start, h.end) for h in group]))
            for (amount, currency), group in list(groups.items())[:MAX_CANDIDATES]
        )
        return failure(ParseError.MULTIPLE_AMOUNTS, candidates=candidates)

    (amount, currency), group = next(iter(groups.items()))
    return ParseResult(
        amount=amount,
        currency=currency,
        type=entry_type,
        note=_make_note(body, [(h.start, h.end) for h in group]),
        needs_confirmation=group[0].major > LARGE_AMOUNT_MAJOR,
    )


def is_large_amount(amount: int, currency: str) -> bool:
    """True when a minor-unit amount is above LARGE_AMOUNT_MAJOR (needs confirmation)."""
    return amount > LARGE_AMOUNT_MAJOR * 10 ** CURRENCY_EXPONENTS[currency]
