import csv
import io

import pytest

from app.core.csv_export import BOM, DELIMITER, build_csv, format_decimal, neutralize_formula


def parse(data: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(data.decode("utf-8-sig"), newline=""), delimiter=";"))


def test_the_file_starts_with_a_utf8_bom_so_excel_reads_cyrillic():
    data = build_csv(["a"], [["b"]])
    assert data.startswith(b"\xef\xbb\xbf")
    assert data.decode("utf-8").startswith(BOM)


def test_semicolon_delimiter_and_crlf_line_ends():
    data = build_csv(["a", "b"], [["1", "2"], ["3", "4"]]).decode("utf-8-sig")
    assert DELIMITER == ";"
    assert data == "a;b\r\n1;2\r\n3;4\r\n"


def test_cyrillic_and_uzbek_round_trip():
    rows = [["\u0415\u0434\u0430", "o'zbek \u2014 so\u2018m", "\U0001F35E"]]
    assert parse(build_csv(["\u0414\u0430\u0442\u0430", "x", "y"], rows)) == [["\u0414\u0430\u0442\u0430", "x", "y"], rows[0]]


def test_cells_with_the_delimiter_quotes_or_newlines_stay_in_one_cell():
    tricky = ["a;b", 'say "hi"', "line1\nline2"]
    assert parse(build_csv(["1", "2", "3"], [tricky]))[1] == tricky


@pytest.mark.parametrize(
    "amount,currency,expected",
    [
        (10000, "UZS", "10000"),
        (0, "UZS", "0"),
        (-500000, "UZS", "-500000"),
        (5050, "USD", "50,50"),
        (5000, "USD", "50,00"),
        (5, "EUR", "0,05"),
        (-5000, "RUB", "-50,00"),
        (123456789, "USD", "1234567,89"),
    ],
)
def test_format_decimal(amount, currency, expected):
    assert format_decimal(amount, currency) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("bread", "bread"),
        ("=1+1", "'=1+1"),
        ("+998901234567", "'+998901234567"),
        ("-cmd", "'-cmd"),
        ("@SUM(A1)", "'@SUM(A1)"),
        ("\tx", "'\tx"),
        (None, ""),
        ("", ""),
    ],
)
def test_formulas_in_text_are_neutralized(text, expected):
    assert neutralize_formula(text) == expected
