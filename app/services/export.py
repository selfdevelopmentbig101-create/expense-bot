"""CSV export of everything the user recorded."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.csv_export import build_csv, format_decimal, neutralize_formula
from app.core.debts import signed_amount
from app.db.models import User
from app.i18n import t
from app.services.categories import category_name
from app.services.debts import all_debt_entries
from app.services.transactions import all_transactions
from app.utils.timezone import to_local


def _when(dt, tz_name: str) -> str:
    return to_local(dt, tz_name).strftime("%Y-%m-%d %H:%M")


async def export_transactions_csv(session: AsyncSession, user: User) -> bytes | None:
    """Income and expenses, oldest first. None when there is nothing to export."""
    rows = await all_transactions(session, user.id)
    if not rows:
        return None
    lang = user.language
    headers = [t(lang, f"export.col.{key}") for key in ("date", "type", "category", "amount", "currency", "note")]
    body = [
        [
            _when(r.created_at, user.timezone),
            t(lang, f"category.type.{r.type}"),
            neutralize_formula(category_name(lang, r.name_key, r.name)),
            format_decimal(r.amount, r.currency),
            r.currency,
            neutralize_formula(r.note),
        ]
        for r in rows
    ]
    return build_csv(headers, body)


async def export_debts_csv(session: AsyncSession, user: User) -> bytes | None:
    """Debt entries as a SEPARATE file (debts are not income or expenses)."""
    rows = await all_debt_entries(session, user.id)
    if not rows:
        return None
    lang = user.language
    keys = ("date", "person", "kind", "amount", "currency", "balance_change", "due", "note")
    headers = [t(lang, f"export.col.{key}") for key in keys]
    body = [
        [
            _when(r.created_at, user.timezone),
            neutralize_formula(r.person_name),
            t(lang, f"export.kind.{r.kind}"),
            format_decimal(r.amount, r.currency),
            r.currency,
            format_decimal(signed_amount(r.kind, r.amount), r.currency),
            r.due_date.strftime("%Y-%m-%d") if r.due_date else "",
            neutralize_formula(r.note),
        ]
        for r in rows
    ]
    return build_csv(headers, body)
