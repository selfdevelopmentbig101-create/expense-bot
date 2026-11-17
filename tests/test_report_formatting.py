from datetime import datetime, timezone

from app.services.report_formatting import MAX_BLOCK_LINES, render_report
from app.services.reports import CategoryTotal
from app.utils.timezone import local_month_bounds, local_week_bounds

TZ = "Asia/Tashkent"
NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)
WEEK = local_week_bounds(NOW, TZ)
MONTH = local_month_bounds(NOW, TZ)

FOOD = ("cat.food", "Food", "\U0001F35E")
TRANSPORT = ("cat.transport", "Transport", "\U0001F695")
OTHER = ("cat.other", "Other", "\U0001F4E6")
SALARY = ("cat.salary", "Salary", "\U0001F4BC")


def row(kind, category, total, currency="UZS"):
    key, name, emoji = category
    return CategoryTotal(kind, currency, key, name, emoji, total)


def week(rows, lang="en"):
    return render_report(lang, TZ, "week", *WEEK, rows)


def test_empty_period():
    text = week([])
    assert "This week" in text and "16.11.2026 \u2013 22.11.2026" in text
    assert "No records for this period yet" in text


def test_month_title_uses_the_whole_calendar_month():
    text = render_report("en", TZ, "month", *MONTH, [])
    assert "This month" in text and "01.11.2026 \u2013 30.11.2026" in text


def test_breakdown_with_percentages_that_add_up_to_100():
    text = week([
        row("expense", OTHER, 45_000),
        row("expense", FOOD, 200_000),
        row("expense", TRANSPORT, 100_000),
    ])
    assert "Spent: <b>345 000 UZS</b>" in text
    lines = [l for l in text.splitlines() if "\u2014" in l]
    assert lines == [  # biggest first, whatever the input order
        "\U0001F35E Food \u2014 200 000 UZS (58%)",
        "\U0001F695 Transport \u2014 100 000 UZS (29%)",
        "\U0001F4E6 Other \u2014 45 000 UZS (13%)",
    ]


def test_income_has_its_own_block_and_percentages():
    text = week([row("expense", FOOD, 1_000), row("income", SALARY, 2_000_000)])
    assert "Spent: <b>1 000 UZS</b>" in text
    assert "Income: <b>2 000 000 UZS</b>" in text
    assert "\U0001F4BC Salary \u2014 2 000 000 UZS (100%)" in text
    assert text.index("Spent") < text.index("Income")


def test_only_income_means_no_spent_block():
    text = week([row("income", SALARY, 5_000)])
    assert "Spent" not in text and "Income" in text


def test_currencies_get_their_own_sections_and_are_never_mixed():
    text = week([row("expense", FOOD, 45_000), row("expense", FOOD, 5_000, "USD")])
    assert "<b>UZS</b>" in text and "<b>USD</b>" in text
    assert "Spent: <b>45 000 UZS</b>" in text and "Spent: <b>50 USD</b>" in text
    assert "Food \u2014 45 000 UZS (100%)" in text and "Food \u2014 50 USD (100%)" in text


def test_a_single_currency_has_no_heading():
    assert "<b>UZS</b>" not in week([row("expense", FOOD, 1_000)])


def test_many_categories_are_summed_up_at_the_end():
    rows = [row("expense", (None, f"C{i:02d}", "\U0001F4CC"), 1_000) for i in range(1, 13)]
    text = week(rows)
    shown = [l for l in text.splitlines() if l.startswith("\U0001F4CC")]
    assert len(shown) == MAX_BLOCK_LINES - 1
    assert "\u2026 other categories (3) \u2014 3 000 UZS (24%)" in text
    assert "Spent: <b>12 000 UZS</b>" in text


def test_default_categories_are_translated_custom_names_are_escaped():
    text = week([row("expense", FOOD, 1_000), row("expense", (None, "R&D <b>", "\U0001F4CC"), 500)], lang="ru")
    assert "\u0415\u0434\u0430" in text
    assert "R&amp;D &lt;b&gt;" in text
    assert "\u041f\u043e\u0442\u0440\u0430\u0447\u0435\u043d\u043e" in text
