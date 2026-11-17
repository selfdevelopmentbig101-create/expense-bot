"""Debt balance math. Pure logic, no database."""
import pytest

from app.core.debts import (
    DebtKind,
    Direction,
    RepaymentStatus,
    balances,
    check_repayment,
    closing_entry,
    direction,
    new_debt_kind_for,
    open_balances,
    signed_amount,
)

B, L, RBM, RTM = "borrowed", "lent", "repaid_by_me", "repaid_to_me"


@pytest.mark.parametrize(
    "kind,expected",
    [(L, 100), (RBM, 100), (B, -100), (RTM, -100)],
)
def test_signed_values_follow_the_spec(kind, expected):
    assert signed_amount(kind, 100) == expected


def test_unknown_kind_is_rejected():
    with pytest.raises(ValueError):
        signed_amount("gift", 100)


def test_borrowed_means_i_owe_and_lent_means_they_owe():
    assert balances([(B, 500_000, "UZS")]) == {"UZS": -500_000}
    assert balances([(L, 500_000, "UZS")]) == {"UZS": 500_000}
    assert direction(-500_000) is Direction.I_OWE
    assert direction(500_000) is Direction.OWED_TO_ME


def test_partial_repayment_keeps_the_rest_open():
    entries = [(B, 500_000, "UZS"), (RBM, 200_000, "UZS")]
    assert balances(entries) == {"UZS": -300_000}
    check = check_repayment(RBM, 200_000, -500_000)
    assert check.status is RepaymentStatus.OK
    assert (check.owed, check.rest) == (500_000, -300_000)


def test_partial_repayment_to_me():
    entries = [(L, 500_000, "UZS"), (RTM, 100_000, "UZS"), (RTM, 150_000, "UZS")]
    assert balances(entries) == {"UZS": 250_000}


def test_full_repayment_closes_the_debt():
    entries = [(B, 500_000, "UZS"), (RBM, 200_000, "UZS"), (RBM, 300_000, "UZS")]
    result = balances(entries)
    assert result == {"UZS": 0}
    assert open_balances(result) == {}  # hidden from the active list
    assert direction(0) is Direction.CLOSED


def test_exact_repayment_is_not_an_overpayment():
    assert check_repayment(RBM, 500_000, -500_000).status is RepaymentStatus.OK
    assert check_repayment(RTM, 500_000, 500_000).status is RepaymentStatus.OK


def test_overpayment_by_me_needs_confirmation_and_flips_the_balance():
    check = check_repayment(RBM, 150_000, -100_000)
    assert check.status is RepaymentStatus.OVERPAYMENT
    assert (check.owed, check.rest) == (100_000, 50_000)  # now THEY owe me 50 000


def test_overpayment_to_me_needs_confirmation_and_flips_the_balance():
    check = check_repayment(RTM, 150_000, 100_000)
    assert check.status is RepaymentStatus.OVERPAYMENT
    assert (check.owed, check.rest) == (100_000, -50_000)  # now I owe THEM 50 000


def test_repayment_without_a_debt():
    check = check_repayment(RBM, 100_000, 0)
    assert check.status is RepaymentStatus.NO_DEBT
    assert (check.owed, check.rest) == (0, 100_000)
    assert check_repayment(RTM, 100_000, 0).status is RepaymentStatus.NO_DEBT


def test_repayment_in_the_wrong_direction_has_no_matching_debt():
    # they owe me, so "I repaid" has nothing to repay; and the reverse
    assert check_repayment(RBM, 100, 5_000).status is RepaymentStatus.NO_DEBT
    assert check_repayment(RTM, 100, -5_000).status is RepaymentStatus.NO_DEBT


def test_only_repayments_can_be_checked():
    with pytest.raises(ValueError):
        check_repayment(B, 100, 0)


def test_two_currencies_with_one_person_never_mix():
    entries = [
        (B, 500_000, "UZS"),
        (L, 100_00, "USD"),
        (RBM, 200_000, "UZS"),
    ]
    assert balances(entries) == {"UZS": -300_000, "USD": 10_000}
    # a USD repayment is judged against the USD balance only
    usd = check_repayment(RTM, 4_000, 10_000)
    assert usd.status is RepaymentStatus.OK and usd.rest == 6_000
    # I owe UZS but not USD: repaying in USD has no matching debt
    assert check_repayment(RBM, 5_000, 10_000).status is RepaymentStatus.NO_DEBT


def test_closing_a_debt_writes_the_entry_that_reaches_zero():
    assert closing_entry(300_000) == (DebtKind.REPAID_TO_ME, 300_000)
    assert closing_entry(-300_000) == (DebtKind.REPAID_BY_ME, 300_000)
    assert closing_entry(0) is None
    for start in (300_000, -300_000):
        kind, amount = closing_entry(start)
        assert start + signed_amount(kind, amount) == 0


def test_a_repayment_without_debt_becomes_the_opposite_new_debt_with_the_same_effect():
    assert new_debt_kind_for(RBM) is DebtKind.LENT
    assert new_debt_kind_for(RTM) is DebtKind.BORROWED
    for repaid in (RBM, RTM):
        assert signed_amount(repaid, 700) == signed_amount(new_debt_kind_for(repaid), 700)
    with pytest.raises(ValueError):
        new_debt_kind_for(B)


def test_no_entries_means_no_balances():
    assert balances([]) == {}
