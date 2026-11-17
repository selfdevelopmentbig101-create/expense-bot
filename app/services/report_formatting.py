"""Text of /week and /month."""
import html
from datetime import datetime

from app.core.dates import format_user_date
from app.core.money import format_amount
from app.core.stats import percentages
from app.i18n import t
from app.services.categories import category_name
from app.services.reports import CategoryTotal
from app.utils.timezone import local_dates

MAX_BLOCK_LINES = 10


def _render_block(lang: str, key: str, rows: list[CategoryTotal], currency: str) -> str:
    ordered = sorted(rows, key=lambda r: (-r.total, r.name.casefold()))
    total = sum(r.total for r in ordered)
    shares = percentages([r.total for r in ordered])

    lines = [t(lang, key, total=format_amount(total, currency))]
    shown = ordered if len(ordered) <= MAX_BLOCK_LINES else ordered[: MAX_BLOCK_LINES - 1]
    for row, share in zip(shown, shares):
        name = html.escape(category_name(lang, row.name_key, row.name))
        lines.append(f"{row.emoji} {name} \u2014 {format_amount(row.total, currency)} ({share}%)")

    rest = ordered[len(shown) :]
    if rest:  # too many categories: the small ones are summed up
        rest_total = sum(r.total for r in rest)
        rest_share = sum(shares[len(shown) :])
        label = t(lang, "report.others", count=len(rest))
        lines.append(f"{label} \u2014 {format_amount(rest_total, currency)} ({rest_share}%)")
    return "\n".join(lines)


def render_report(
    lang: str,
    tz_name: str,
    period: str,
    start: datetime,
    end: datetime,
    rows: list[CategoryTotal],
) -> str:
    """period is "week" or "month". Each currency gets its own section."""
    first, last = local_dates(start, end, tz_name)
    title = t(lang, f"report.{period}", start=format_user_date(first), end=format_user_date(last))
    if not rows:
        return f"{title}\n\n{t(lang, 'report.empty')}"

    currencies = sorted({r.currency for r in rows})
    sections = []
    for currency in currencies:
        parts = [f"<b>{currency}</b>"] if len(currencies) > 1 else []
        for entry_type, key in (("expense", "report.spent"), ("income", "report.income")):
            block = [r for r in rows if r.currency == currency and r.type == entry_type]
            if block:
                parts.append(_render_block(lang, key, block, currency))
        sections.append("\n\n".join(parts))
    return title + "\n\n" + "\n\n".join(sections)
