import operator

import pytest

from jaraco.itertools import assert_ordered


@pytest.mark.parametrize('values', [[], [1], [None], [1, 2, 3]])
@pytest.mark.parametrize('factory', [list, iter])
def test_ordered_preserves_short_inputs(values, factory):
    assert list(assert_ordered(factory(values))) == values


def test_ordered_rejects_disordered_pair():
    with pytest.raises(AssertionError, match='2 > 1'):
        list(assert_ordered([2, 1]))


def test_ordered_custom_comparison():
    assert list(assert_ordered([3, 2, 1], comp=operator.ge)) == [3, 2, 1]
    assert list(assert_ordered(['a', 'bb'], key=len)) == ['a', 'bb']
