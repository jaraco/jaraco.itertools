from operator import itemgetter

from jaraco.itertools import collate_revs


def test_reordered_revisions_prefer_new_values():
    old = [('a', 1), ('b', 1), ('c', 1)]
    new = [('c', 2), ('b', 2), ('a', 2)]

    assert list(collate_revs(old, new, key=itemgetter(0))) == new


def test_reordered_merge_receives_old_then_new():
    old = [('a', 1), ('b', 1), ('old-only', 1)]
    new = [('new-only', 2), ('b', 2), ('a', 2)]
    calls = []

    def merge(previous, current):
        calls.append((previous, current))
        return current[0], previous[1] + current[1]

    assert list(collate_revs(old, new, key=itemgetter(0), merge=merge)) == [
        ('new-only', 2),
        ('b', 3),
        ('a', 3),
        ('old-only', 1),
    ]
    assert calls == [(('b', 1), ('b', 2)), (('a', 1), ('a', 2))]
