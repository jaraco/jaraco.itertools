import pytest

from jaraco.itertools import collate_revs


@pytest.mark.parametrize('value', [0, False, None, ''])
def test_matching_falsy_revision_keeps_new_order(value):
    old = ['before', value, 'after']
    new = [value, 'after']
    assert list(collate_revs(old, new)) == old


def test_falsy_revision_at_start_preserves_unmatched_old_items():
    assert list(collate_revs([0, 1, 2], [0, 2])) == [0, 1, 2]


def test_falsy_matches_are_merged_in_order():
    merged = []

    def merge(old, new):
        merged.append((old, new))
        return new

    assert list(collate_revs([0, 1, None, ''], [0, None, ''], merge=merge)) == [
        0,
        1,
        None,
        '',
    ]
    assert merged == [(0, 0), (None, None), ('', '')]
