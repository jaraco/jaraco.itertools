import pytest

from jaraco.itertools import window


@pytest.mark.parametrize('pre,post', [(0, 1), (1, 0), (0, 0), (2, 1)])
@pytest.mark.parametrize('values', [[], [1], [1, 2, 3]])
def test_window_context_widths(pre, post, values):
    result = list(window(iter(values), pre_size=pre, post_size=post))
    assert [item for _, item, _ in result] == values
    assert all(len(before) == pre and len(after) == post for before, _, after in result)
