"""CSV for Excel: UTF-8 with BOM, ';' as the delimiter, CRLF line ends.

The delimiter is ';' and decimals use a comma, which is what Excel expects with Russian
and Uzbek regional settings (a ',' delimiter would put everything into one column).
"""
import csv
import io

from app.core.money import CURRENCY_EXPONENTS

BOM = "\ufeff"
DELIMITER = ";"
_DANGEROUS_START = ("=", "+", "-", "@", "\t", "\r")


def format_decimal(amount: int, currency: str) -> str:
    """10000 UZS -> "10000"; 5050 USD -> "50,50"; -5000 USD -> "-50,00". Plain numbers only."""
    exponent = CURRENCY_EXPONENTS.get(currency, 0)
    sign = "-" if amount < 0 else ""
    major, minor = divmod(abs(amount), 10**exponent)
    if exponent == 0:
        return f"{sign}{major}"
    return f"{sign}{major},{minor:0{exponent}d}"


def neutralize_formula(text: str | None) -> str:
    """Stop Excel from running a note like "=HYPERLINK(...)" as a formula."""
    if not text:
        return ""
    if text.startswith(_DANGEROUS_START):
        return "'" + text
    return text


def build_csv(headers: list[str], rows: list[list[str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=DELIMITER, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return (BOM + buffer.getvalue()).encode("utf-8")
