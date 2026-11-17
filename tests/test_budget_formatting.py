from datetime import datetime, timezone

from app.core.budgets import BudgetAlert
from app.services.budget_formatting import render_budget_alert, render_budgets
from app.services.budgets import BudgetProgress, BudgetStatus
from app.utils.timezone import local_month_bounds

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)
TZ = "Asia/Tashkent"
START, END = local_month_bounds(NOW, TZ)


def item(spent, limit=300_000, name_key="cat.food", name="Food", currency="UZS"):
    return BudgetProgress(1, name_key, name, "\U0001F35E", limit, currency, spent)


def test_empty():
    text = render_budgets("en", TZ, START, END, [])
    assert "01.11.2026 \u2013 30.11.2026" in text and "80%" in text


def test_budget_lines_with_progress_bars():
    text = render_budgets("en", TZ, START, END, [item(120_000)])
    assert "\U0001F35E Food: 120 000 UZS of 300 000 UZS (40%)" in text
    assert "\u2593\u2593\u2593\u2593\u2591\u2591\u2591\u2591\u2591\u2591" in text


def test_names_are_translated_or_escaped():
    assert "\u0415\u0434\u0430" in render_budgets("ru", TZ, START, END, [item(1)])
    assert "R&amp;D" in render_budgets("en", TZ, START, END, [item(1, name_key=None, name="R&D")])


def test_over_the_limit_still_renders():
    text = render_budgets("en", TZ, START, END, [item(450_000)])
    assert "(150%)" in text


def test_alert_texts():
    warning = BudgetStatus(BudgetAlert.WARNING, 246_000, 300_000, 82, "UZS")
    text = render_budget_alert("en", warning, "cat.food", "Food", "\U0001F35E")
    assert text.startswith("\u26a0\ufe0f") and "82%" in text and "246 000 UZS of 300 000 UZS" in text
    exceeded = BudgetStatus(BudgetAlert.EXCEEDED, 310_000, 300_000, 103, "UZS")
    text = render_budget_alert("en", exceeded, "cat.food", "Food", "\U0001F35E")
    assert text.startswith("\U0001F6A8") and "103%" in text
    assert "Oziq-ovqat" in render_budget_alert("uz", exceeded, "cat.food", "Food", "\U0001F35E")
