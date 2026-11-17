import pytest

from app.core.stats import percentages


@pytest.mark.parametrize(
    "values,expected",
    [
        ([1, 1, 1], [34, 33, 33]),
        ([50, 50], [50, 50]),
        ([1, 2], [33, 67]),
        ([5], [100]),
        ([200_000, 100_000, 45_000], [58, 29, 13]),
        ([0, 0], [0, 0]),
        ([], []),
        ([0, 10], [0, 100]),
    ],
)
def test_percentages(values, expected):
    assert percentages(values) == expected


@pytest.mark.parametrize(
    "values",
    [
        [1] * 7,
        [3, 3, 3, 3, 3, 3],
        [999_999, 1],
        [10**12, 10**12 + 1, 7],
        list(range(1, 25)),
    ],
)
def test_shares_always_add_up_to_exactly_100(values):
    result = percentages(values)
    assert sum(result) == 100
    assert all(0 <= share <= 100 for share in result)


def test_the_order_of_the_input_is_kept():
    assert percentages([10, 70, 20]) == [10, 70, 20]
