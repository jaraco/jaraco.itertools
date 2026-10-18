from jaraco.itertools import Peekable


def test_rewrapping_preserves_peeked_items():
    original = Peekable([1, 2, 3])
    assert original.peek() == 1
    wrapped = Peekable(original)
    assert wrapped is original
    assert wrapped.peek() == 1
    assert next(wrapped) == 1
    assert list(original) == [2, 3]


def test_rewrapping_exhausted_iterator():
    original = Peekable([])
    assert Peekable(original) is original
    assert list(original) == []
