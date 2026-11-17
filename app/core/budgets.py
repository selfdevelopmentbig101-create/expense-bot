"""Budget math. Pure logic.

A budget is a recurring MONTHLY limit for one expense category.
The user is warned once when spending crosses 80% and once when it reaches 100%.
"""
from enum import StrEnum

WARN_PERCENT = 80


class BudgetAlert(StrEnum):
    WARNING = "warning"  # crossed 80%
    EXCEEDED = "exceeded"  # reached or passed 100%


def percent_used(spent: int, limit: int) -> int:
    """Whole percent of the limit already used (rounded down)."""
    if limit <= 0:
        return 0
    return spent * 100 // limit


def crossing_alert(spent_before: int, spent_after: int, limit: int) -> BudgetAlert | None:
    """The alert caused by ONE new expense, or None.

    Only crossing a threshold alerts, so a user already over the limit is not nagged on
    every purchase. If one expense crosses both thresholds, only the 100% alert is sent.
    """
    if limit <= 0 or spent_after <= spent_before:
        return None
    if spent_before < limit <= spent_after:
        return BudgetAlert.EXCEEDED
    if spent_before * 100 < limit * WARN_PERCENT <= spent_after * 100 and spent_after < limit:
        return BudgetAlert.WARNING
    return None


def progress_bar(percent: int, width: int = 10) -> str:
    filled = max(0, min(width, percent * width // 100))
    return "\u2593" * filled + "\u2591" * (width - filled)
