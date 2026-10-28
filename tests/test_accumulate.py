import copy
import itertools

import pytest

from jaraco.itertools import accumulate


@pytest.mark.parametrize(
    'values', [[[1], [2], [3]], [[], [1], [2]], [1, 2, 3], ['a', 'b', 'c']]
)
def test_accumulate_matches_addition_without_mutating_inputs(values):
    original = copy.deepcopy(values)
    expected = list(itertools.accumulate(copy.deepcopy(values)))
    assert list(accumulate(iter(values))) == expected
    assert values == original
