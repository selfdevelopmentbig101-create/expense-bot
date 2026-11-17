import pytest

from app.core.money import format_amount


@pytest.mark.parametrize(
    "amount,currency,expected",
    [
        (0, "UZS", "0 UZS"),
        (999, "UZS", "999 UZS"),
        (10000, "UZS", "10 000 UZS"),
        (1500000, "UZS", "1 500 000 UZS"),
        (-10000, "UZS", "-10 000 UZS"),
        (5000, "USD", "50 USD"),
        (5050, "USD", "50.50 USD"),
        (5, "USD", "0.05 USD"),
        (123456789, "EUR", "1 234 567.89 EUR"),
        (100, "XXX", "100 XXX"),  # unknown code: no decimals, never crashes
    ],
)
def test_format_amount(amount, currency, expected):
    assert format_amount(amount, currency) == expected
