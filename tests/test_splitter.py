import pytest

from jaraco.itertools import splitter


@pytest.mark.parametrize(
    'text, separator',
    [
        ('a::b::c', '::'),
        ('::a::::', '::'),
        ('aaaaa', 'aa'),
        ('a<>b<>', '<>'),
        ('a💫💫b', '💫💫'),
        ('', '::'),
        ('no delimiter', '::'),
        ('a,b,', ','),
    ],
)
def test_explicit_separator(text, separator):
    assert list(splitter(separator)(text)) == text.split(separator)


def test_empty_separator():
    with pytest.raises(ValueError, match='empty separator'):
        next(splitter('')('abc'))
