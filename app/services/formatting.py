"""Turning records into Telegram HTML text."""
import html
from datetime import datetime

from app.core.money import format_amount
from app.i18n import t
from app.services.categories import category_name
from app.services.transactions import TransactionView
from app.utils.timezone import format_date, format_time

MAX_TODAY_LINES = 25
NOTE_MAX = 200


def note_suffix(note: str | None) -> str:
    """" (bread)" or an empty string. Notes are user text, so they are escaped."""
    if not note:
        return ""
    return f" ({html.escape(note[:NOTE_MAX])})"


def signed_amount(entry_type: str, amount: int, currency: str) -> str:
    sign = "+" if entry_type == "income" else ""
    return f"{sign}{format_amount(amount, currency)}"


def describe_entry(lang: str, view: TransactionView) -> str:
    """Example: 10 000 UZS - Food (bread)."""
    name = html.escape(category_name(lang, view.name_key, view.name))
    amount = signed_amount(view.type, view.amount, view.currency)
    return f"{amount} \u2014 {name}{note_suffix(view.note)}"


def format_totals(totals: dict[str, int]) -> str:
    return ", ".join(format_amount(totals[code], code) for code in sorted(totals))


def _sum_by_currency(rows: list[TransactionView], entry_type: str) -> dict[str, int]:
    totals: dict[str, int] = {}
    for row in rows:
        if row.type == entry_type:
            totals[row.currency] = totals.get(row.currency, 0) + row.amount
    return totals


def render_today(lang: str, tz_name: str, now: datetime, rows: list[TransactionView]) -> str:
    title = t(lang, "today.title", date=format_date(now, tz_name))
    if not rows:
        return f"{title}\n\n{t(lang, 'today.empty')}"

    shown = rows[-MAX_TODAY_LINES:]
    lines = []
    if len(rows) > len(shown):
        lines.append(t(lang, "today.more", count=len(rows) - len(shown)))
    for row in shown:
        name = html.escape(category_name(lang, row.name_key, row.name))
        amount = signed_amount(row.type, row.amount, row.currency)
        lines.append(
            f"{format_time(row.created_at, tz_name)} {row.emoji} {name} \u2014 {amount}"
            f"{note_suffix(row.note)}"
        )

    footer = []
    spent = _sum_by_currency(rows, "expense")
    income = _sum_by_currency(rows, "income")
    if spent:
        footer.append(t(lang, "today.spent", total=format_totals(spent)))
    if income:
        footer.append(t(lang, "today.income", total=format_totals(income)))
    return title + "\n\n" + "\n".join(lines) + "\n\n" + "\n".join(footer)
