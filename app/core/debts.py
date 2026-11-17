"""Debt math. Pure logic: no Telegram, no database.

Every debt entry has a SIGNED value:
    lent          +amount   (the person owes me more)
    repaid_by_me  +amount   (I paid back what I owed: moves my balance towards zero)
    borrowed      -amount   (I owe the person more)
    repaid_to_me  -amount   (they paid me back)
Balance per person AND currency = sum of signed values.
    positive = the person owes me, negative = I owe the person, zero = closed.
Currencies are never mixed: every function works with one dict per currency.
"""
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum


class DebtKind(StrEnum):
    BORROWED = "borrowed"  # I borrowed: I owe the person
    LENT = "lent"  # I lent: the person owes me
    REPAID_BY_ME = "repaid_by_me"  # I paid back
    REPAID_TO_ME = "repaid_to_me"  # they paid me back


NEW_DEBT_KINDS = (DebtKind.BORROWED, DebtKind.LENT)
REPAYMENT_KINDS = (DebtKind.REPAID_BY_ME, DebtKind.REPAID_TO_ME)

_SIGN = {
    DebtKind.LENT: 1,
    DebtKind.REPAID_BY_ME: 1,
    DebtKind.BORROWED: -1,
    DebtKind.REPAID_TO_ME: -1,
}


def signed_amount(kind: str, amount: int) -> int:
    return _SIGN[DebtKind(kind)] * amount


def balances(entries: Iterable[tuple[str, int, str]]) -> dict[str, int]:
    """entries are (kind, amount, currency). Returns the signed balance per currency."""
    result: dict[str, int] = {}
    for kind, amount, currency in entries:
        result[currency] = result.get(currency, 0) + signed_amount(kind, amount)
    return result


def open_balances(all_balances: dict[str, int]) -> dict[str, int]:
    """Drop closed (zero) balances. A zero balance means the debt is closed."""
    return {currency: value for currency, value in all_balances.items() if value != 0}


class Direction(StrEnum):
    I_OWE = "i_owe"
    OWED_TO_ME = "owed_to_me"
    CLOSED = "closed"


def direction(balance: int) -> Direction:
    if balance < 0:
        return Direction.I_OWE
    if balance > 0:
        return Direction.OWED_TO_ME
    return Direction.CLOSED


class RepaymentStatus(StrEnum):
    OK = "ok"
    NO_DEBT = "no_debt"  # nothing to repay in this direction
    OVERPAYMENT = "overpayment"  # more than the debt


@dataclass(frozen=True, slots=True)
class RepaymentCheck:
    status: RepaymentStatus
    owed: int  # size of the matching debt (0 when there is none)
    rest: int  # signed balance AFTER the repayment would be recorded


def check_repayment(kind: str, amount: int, balance: int) -> RepaymentCheck:
    """Does this repayment match an existing debt in the same currency?"""
    kind = DebtKind(kind)
    if kind is DebtKind.REPAID_BY_ME:
        owed = -balance if balance < 0 else 0
    elif kind is DebtKind.REPAID_TO_ME:
        owed = balance if balance > 0 else 0
    else:
        raise ValueError(f"{kind} is not a repayment")

    rest = balance + signed_amount(kind, amount)
    if owed == 0:
        status = RepaymentStatus.NO_DEBT
    elif amount > owed:
        status = RepaymentStatus.OVERPAYMENT
    else:
        status = RepaymentStatus.OK
    return RepaymentCheck(status, owed, rest)


def new_debt_kind_for(kind: str) -> DebtKind:
    """A repayment with no matching debt can be recorded as a new debt instead.

    "I repaid Aziz" with no debt means I gave him money: he owes me (lent).
    "Bobur repaid me" with no debt means he gave me money: I owe him (borrowed).
    The signed value stays the same, so the balance is identical either way.
    """
    kind = DebtKind(kind)
    if kind is DebtKind.REPAID_BY_ME:
        return DebtKind.LENT
    if kind is DebtKind.REPAID_TO_ME:
        return DebtKind.BORROWED
    raise ValueError(f"{kind} is not a repayment")


def closing_entry(balance: int) -> tuple[DebtKind, int] | None:
    """The entry that brings a balance to exactly zero, or None if already closed."""
    if balance > 0:
        return DebtKind.REPAID_TO_ME, balance
    if balance < 0:
        return DebtKind.REPAID_BY_ME, -balance
    return None
