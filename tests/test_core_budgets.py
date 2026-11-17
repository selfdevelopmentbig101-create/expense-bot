import pytest

from app.core.budgets import BudgetAlert, crossing_alert, percent_used, progress_bar

W, X = BudgetAlert.WARNING, BudgetAlert.EXCEEDED


@pytest.mark.parametrize(
    "spent,limit,expected",
    [(0, 1000, 0), (799, 1000, 79), (800, 1000, 80), (1000, 1000, 100), (1500, 1000, 150), (5, 0, 0)],
)
def test_percent_used(spent, limit, expected):
    assert percent_used(spent, limit) == expected


@pytest.mark.parametrize(
    "before,after,expected",
    [
        (0, 500, None),  # 50%: nothing to say
        (790, 800, W),  # crossing 80% exactly
        (799, 800, W),
        (800, 801, None),  # already past 80%: no second warning
        (500, 850, W),
        (850, 999, None),
        (999, 1000, X),  # reaching 100% exactly
        (500, 1000, X),
        (500, 1500, X),  # one big expense crosses both: only the 100% alert
        (0, 5000, X),
        (1000, 1200, None),  # already over: not nagged on every purchase
        (900, 900, None),  # nothing was added
    ],
)
def test_crossing_alert(before, after, expected):
    assert crossing_alert(before, after, 1000) is expected


def test_no_limit_means_no_alert():
    assert crossing_alert(0, 100, 0) is None


def test_progress_bar():
    assert progress_bar(0) == "\u2591" * 10
    assert progress_bar(40) == "\u2593" * 4 + "\u2591" * 6
    assert progress_bar(100) == "\u2593" * 10
    assert progress_bar(250) == "\u2593" * 10  # over the limit: the bar is simply full
