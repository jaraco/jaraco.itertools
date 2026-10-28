import pytest

from jaraco.itertools import bisect


@pytest.mark.parametrize('values', [[1, 0, 2, 0], [0, 1, 0, 2], [1, 2], [0, 0], []])
def test_bisect_returns_false_then_true(values):
    false, true = bisect(iter(values))
    assert list(false) == [value for value in values if not value]
    assert list(true) == [value for value in values if value]


def test_bisect_uses_predicate_truth_value():
    values = [3, 0, 1, 2, 0]
    false, true = bisect(iter(values), lambda value: value)
    assert list(false) == [0, 0]
    assert list(true) == [3, 1, 2]
