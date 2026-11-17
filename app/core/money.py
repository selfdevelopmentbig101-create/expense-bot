"""Currencies. Money is always stored as an integer in MINOR units.

UZS is treated as having no minor units (tiyin are not used in practice);
USD, EUR and RUB have 2 decimals (cents).
"""
DEFAULT_CURRENCY = "UZS"

# currency code -> number of decimal digits in its minor unit
CURRENCY_EXPONENTS: dict[str, int] = {"UZS": 0, "USD": 2, "EUR": 2, "RUB": 2}

SUPPORTED_CURRENCIES: tuple[str, ...] = tuple(CURRENCY_EXPONENTS)


def format_amount(amount: int, currency: str) -> str:
    """10000 UZS -> "10 000 UZS", 5050 USD -> "50.50 USD", 5000 USD -> "50 USD"."""
    exponent = CURRENCY_EXPONENTS.get(currency, 0)
    sign = "-" if amount < 0 else ""
    major, minor = divmod(abs(amount), 10**exponent)
    text = f"{major:,}".replace(",", " ")
    if exponent and minor:
        text += f".{minor:0{exponent}d}"
    return f"{sign}{text} {currency}"
