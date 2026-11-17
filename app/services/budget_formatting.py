"""Text of /budget and the warnings after saving an expense."""
import html
from datetime import datetime

from app.core.budgets import BudgetAlert, progress_bar
from app.core.dates import format_user_date
from app.core.money import format_amount
from app.i18n import t
from app.services.budgets import BudgetProgress, BudgetStatus
from app.services.categories import category_name
from app.utils.timezone import local_dates


def render_budgets(
    lang: str, tz_name: str, start: datetime, end: datetime, items: list[BudgetProgress]
) -> str:
    first, last = local_dates(start, end, tz_name)
    title = t(lang, "budget.title", start=format_user_date(first), end=format_user_date(last))
    if not items:
        return f"{title}\n\n{t(lang, 'budget.empty')}"

    lines = []
    for item in items:
        name = html.escape(category_name(lang, item.name_key, item.name))
        lines.append(
            t(
                lang,
                "budget.line",
                emoji=item.emoji,
                name=name,
                spent=format_amount(item.spent, item.currency),
                limit=format_amount(item.limit, item.currency),
                percent=item.percent,
            )
            + "\n"
            + progress_bar(item.percent)
        )
    return f"{title}\n\n" + "\n\n".join(lines) + f"\n\n{t(lang, 'budget.hint')}"


def render_budget_alert(
    lang: str, status: BudgetStatus, name_key: str | None, name: str, emoji: str
) -> str:
    key = "budget.alert.exceeded" if status.alert is BudgetAlert.EXCEEDED else "budget.alert.warning"
    return t(
        lang,
        key,
        emoji=emoji,
        name=html.escape(category_name(lang, name_key, name)),
        percent=status.percent,
        spent=format_amount(status.spent, status.currency),
        limit=format_amount(status.limit, status.currency),
    )
