from datetime import datetime, timezone

from app.services.formatting import (
    MAX_TODAY_LINES,
    describe_entry,
    note_suffix,
    render_today,
)
from app.services.transactions import TransactionView

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)  # 17:00 in Tashkent
TZ = "Asia/Tashkent"


def view(entry_type="expense", amount=10000, currency="UZS", note=None,
         name_key="cat.food", name="Food", emoji="\U0001F35E", minutes=0):
    created = NOW.replace(minute=minutes)
    return TransactionView(1, entry_type, amount, currency, note, created, name_key, name, emoji)


def test_note_suffix():
    assert note_suffix(None) == ""
    assert note_suffix("") == ""
    assert note_suffix("bread") == " (bread)"


def test_note_is_html_escaped():
    assert note_suffix("<b>hi</b> & co") == " (&lt;b&gt;hi&lt;/b&gt; &amp; co)"


def test_describe_entry_expense_and_income():
    assert describe_entry("en", view(note="bread")) == "10 000 UZS \u2014 Food (bread)"
    income = view("income", 2000000, name_key="cat.salary", name="Salary")
    assert describe_entry("en", income) == "+2 000 000 UZS \u2014 Salary"


def test_default_categories_are_translated_and_custom_ones_are_not():
    assert describe_entry("ru", view()) == "10 000 UZS \u2014 \u0415\u0434\u0430"
    custom = view(name_key=None, name="R&D")
    assert describe_entry("ru", custom) == "10 000 UZS \u2014 R&amp;D"


def test_render_today_empty():
    text = render_today("en", TZ, NOW, [])
    assert "17.11.2026" in text
    assert "No records today yet" in text


def test_render_today_lists_records_and_totals():
    rows = [
        view(amount=10000, note="bread", minutes=0),
        view(amount=35000, name_key="cat.transport", name="Transport", emoji="\U0001F695", minutes=5),
        view("income", 2000000, name_key="cat.salary", name="Salary", emoji="\U0001F4BC", minutes=10),
    ]
    text = render_today("en", TZ, NOW, rows)
    assert "17:00 \U0001F35E Food \u2014 10 000 UZS (bread)" in text
    assert "17:05 \U0001F695 Transport \u2014 35 000 UZS" in text
    assert "+2 000 000 UZS" in text
    assert "Spent: <b>45 000 UZS</b>" in text
    assert "Income: <b>2 000 000 UZS</b>" in text


def test_render_today_never_mixes_currencies():
    rows = [view(amount=45000), view(amount=5000, currency="USD")]
    text = render_today("en", TZ, NOW, rows)
    assert "Spent: <b>50 USD, 45 000 UZS</b>" in text


def test_render_today_without_income_has_no_income_line():
    assert "Income" not in render_today("en", TZ, NOW, [view()])


def test_render_today_is_capped_and_says_how_many_are_hidden():
    rows = [view(minutes=i % 60) for i in range(MAX_TODAY_LINES + 5)]
    text = render_today("en", TZ, NOW, rows)
    assert "\u2026and 5 earlier" in text
    assert text.count(" \u2014 10 000 UZS") == MAX_TODAY_LINES
    # totals still cover ALL records, not only the visible ones
    assert f"Spent: <b>{(MAX_TODAY_LINES + 5) * 10000:,}".replace(",", " ") in text


def test_render_today_in_russian_and_uzbek():
    assert "\u0421\u0435\u0433\u043e\u0434\u043d\u044f" in render_today("ru", TZ, NOW, [view()])
    assert "Bugun" in render_today("uz", TZ, NOW, [view()])
