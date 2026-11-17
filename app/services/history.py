"""/history: the last records of any kind, newest first."""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.money import format_amount
from app.i18n import t
from app.services.categories import category_name
from app.services.debt_formatting import entry_line
from app.services.debts import DebtEntryView, recent_debt_entries
from app.services.formatting import note_suffix, signed_amount
from app.services.transactions import TransactionView, recent_transactions
from app.utils.timezone import format_short

import html

HISTORY_SIZE = 10


@dataclass(frozen=True, slots=True)
class HistoryItem:
    kind: str  # "t" = income/expense record, "d" = debt entry
    id: int
    created_at: datetime
    transaction: TransactionView | None = None
    debt: DebtEntryView | None = None


def merge_recent(
    transactions: list[TransactionView], debts: list[DebtEntryView], limit: int = HISTORY_SIZE
) -> list[HistoryItem]:
    """Newest first. On the same instant a debt entry comes first (same rule as /undo)."""
    items = [HistoryItem("t", v.id, v.created_at, transaction=v) for v in transactions]
    items += [HistoryItem("d", v.id, v.created_at, debt=v) for v in debts]
    items.sort(key=lambda item: (item.created_at, item.kind == "d", item.id), reverse=True)
    return items[:limit]


async def recent_records(
    session: AsyncSession, user_id: int, limit: int = HISTORY_SIZE
) -> list[HistoryItem]:
    transactions = await recent_transactions(session, user_id, limit)
    debts = await recent_debt_entries(session, user_id, limit)
    return merge_recent(transactions, debts, limit)


def render_history(lang: str, tz_name: str, items: list[HistoryItem]) -> str:
    title = t(lang, "history.title")
    if not items:
        return f"{title}\n\n{t(lang, 'history.empty')}"

    lines = []
    for number, item in enumerate(items, start=1):
        when = format_short(item.created_at, tz_name)
        if item.transaction is not None:
            row = item.transaction
            name = html.escape(category_name(lang, row.name_key, row.name))
            amount = signed_amount(row.type, row.amount, row.currency)
            text = f"{row.emoji} {name} \u2014 {amount}{note_suffix(row.note)}"
        else:
            row = item.debt
            text = entry_line(lang, row.kind, row.amount, row.currency, row.person_name)
        lines.append(f"{number}. {when} {text}")
    return f"{title}\n\n" + "\n".join(lines) + f"\n\n{t(lang, 'history.hint')}"
