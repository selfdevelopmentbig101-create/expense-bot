"""Text of the reminder messages."""
import html

from app.core.dates import format_user_date
from app.core.money import format_amount
from app.i18n import t
from app.services.formatting import format_totals
from app.services.reminders import DebtReminder, EveningReminder


def render_debt_reminder(lang: str, reminder: DebtReminder) -> str:
    """Example: Tomorrow you should return 500 000 UZS to Aziz."""
    side = "i_owe" if reminder.balance < 0 else "they_owe"
    return t(
        lang,
        f"reminder.{reminder.kind.value}.{side}",
        amount=format_amount(reminder.amount, reminder.currency),
        person=html.escape(reminder.person_name),
        date=format_user_date(reminder.due),
    )


def render_evening(lang: str, reminder: EveningReminder) -> str:
    text = t(lang, "reminder.evening")
    if reminder.spent_today:
        text += "\n\n" + t(lang, "reminder.evening_total", total=format_totals(reminder.spent_today))
    return text
