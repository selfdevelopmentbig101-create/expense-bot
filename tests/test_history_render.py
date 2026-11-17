from datetime import datetime, timedelta, timezone

from app.services.debts import DebtEntryView
from app.services.history import HISTORY_SIZE, merge_recent, render_history
from app.services.transactions import TransactionView

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)
TZ = "Asia/Tashkent"


def tx(id_, minutes, amount=10_000, note=None, kind="expense"):
    return TransactionView(id_, kind, amount, "UZS", note, NOW + timedelta(minutes=minutes),
                           "cat.food", "Food", "\U0001F35E")


def debt(id_, minutes, kind="borrowed", amount=500_000):
    return DebtEntryView(id_, 1, "Aziz", kind, amount, "UZS", None, None, NOW + timedelta(minutes=minutes))


def test_records_of_both_kinds_are_merged_newest_first():
    items = merge_recent([tx(1, 0), tx(2, 10)], [debt(7, 5)])
    assert [(i.kind, i.id) for i in items] == [("t", 2), ("d", 7), ("t", 1)]


def test_only_the_latest_ten_are_kept():
    items = merge_recent([tx(i, i) for i in range(1, 9)], [debt(i, 100 + i) for i in range(1, 6)])
    assert len(items) == HISTORY_SIZE == 10
    assert items[0].kind == "d" and items[0].id == 5


def test_on_the_same_instant_a_debt_entry_comes_first():
    items = merge_recent([tx(1, 0)], [debt(1, 0)])
    assert [i.kind for i in items] == ["d", "t"]


def test_render_numbers_the_lines_and_shows_both_kinds():
    items = merge_recent([tx(1, 0, note="bread"), tx(2, 10, 2_000_000, kind="income")], [debt(7, 5)])
    text = render_history("en", TZ, items)
    lines = text.splitlines()
    assert "Last records" in lines[0]
    assert lines[2] == "1. 17.11 17:10 \U0001F35E Food \u2014 +2 000 000 UZS"
    assert lines[3] == "2. 17.11 17:05 \U0001F4E5 Borrowed 500 000 UZS from Aziz"
    assert lines[4] == "3. 17.11 17:00 \U0001F35E Food \u2014 10 000 UZS (bread)"
    assert "Tap \U0001F5D1" in text


def test_render_empty_history():
    assert "No records yet" in render_history("en", TZ, [])


def test_render_escapes_user_text():
    text = render_history("en", TZ, merge_recent([tx(1, 0, note="<i>x</i>")], []))
    assert "&lt;i&gt;x&lt;/i&gt;" in text and "<i>" not in text
