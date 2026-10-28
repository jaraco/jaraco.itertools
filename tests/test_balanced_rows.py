import pytest

from jaraco.itertools import balanced_rows


@pytest.mark.parametrize(
    'width,values',
    [(3, 'A'), (5, 'ABCDEF'), (4, 'AB'), (3, 'ABCDEFG'), (3, '')],
)
def test_balanced_rows_padding(width, values):
    rows = list(balanced_rows(width, iter(values), fillvalue=None))
    assert all(len(row) == width for row in rows)
    assert [item for row in rows for item in row if item is not None] == list(values)


def test_balanced_rows_retains_balanced_allocation():
    assert list(balanced_rows(3, 'ABCDEFG', 'x')) == [
        ('A', 'B', 'C'),
        ('D', 'E', 'x'),
        ('F', 'G', 'x'),
    ]
