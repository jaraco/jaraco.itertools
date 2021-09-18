"""
jaraco.itertools
Tools for working with iterables.  Complements itertools and more_itertools.
"""

import operator
import itertools
import collections
import math
import warnings
import functools
import heapq
import collections.abc
import queue

import inflect
import more_itertools


def make_rows(num_columns, seq):
    """
    Make a sequence into rows of num_columns columns.

    >>> tuple(make_rows(2, [1, 2, 3, 4, 5]))
    ((1, 4), (2, 5), (3, None))
    >>> tuple(make_rows(3, [1, 2, 3, 4, 5]))
    ((1, 3, 5), (2, 4, None))
    """
    # calculate the minimum number of rows necessary to fit the list in
    # num_columns Columns
    num_rows, partial = divmod(len(seq), num_columns)
    if partial:
        num_rows += 1
    # break the seq into num_columns of length num_rows
    try:
        result = more_itertools.grouper(seq, num_rows)
    except TypeError:
        # more_itertools before 6.x
        result = more_itertools.grouper(num_rows, seq)
    # result is now a list of columns... transpose it to return a list
    # of rows
    return zip(*result)


def bisect(seq, func=bool):
    """
    Split a sequence into two sequences:  the first is elements that
    return False for func(element) and the second for True for
    func(element).
    By default, func is ``bool``, so uses the truth value of the object.

    >>> is_odd = lambda n: n%2
    >>> even, odd = bisect(range(5), is_odd)
    >>> list(odd)
    [1, 3]
    >>> list(even)
    [0, 2, 4]

    >>> other, zeros = bisect(reversed(range(5)))
    >>> list(zeros)
    [0]
    >>> list(other)
    [4, 3, 2, 1]

    """
    queues = GroupbySaved(seq, func)
    return queues.get_first_n_queues(2)


class GroupbySaved:
    """
    Split a sequence into n sequences where n is determined by the
    number of distinct values returned by a key function applied to each
    element in the sequence.

    >>> truthsplit = GroupbySaved(['Test', '', 30, None], bool)
    >>> truthsplit['x']
    Traceback (most recent call last):
    ...
    KeyError: 'x'
    >>> true_items = truthsplit[True]
    >>> false_items = truthsplit[False]
    >>> tuple(iter(false_items))
    ('', None)
    >>> tuple(iter(true_items))
    ('Test', 30)

    >>> every_third_split = GroupbySaved(range(99), lambda n: n%3)
    >>> zeros = every_third_split[0]
    >>> ones = every_third_split[1]
    >>> twos = every_third_split[2]
    >>> next(zeros)
    0
    >>> next(zeros)
    3
    >>> next(ones)
    1
    >>> next(twos)
    2
    >>> next(ones)
    4
    """

    def __init__(self, sequence, func=lambda x: x):
        self.sequence = iter(sequence)
        self.func = func
        self.queues = collections.OrderedDict()

    def __getitem__(self, key):
        try:
            return self.queues[key]
        except KeyError:
            return self.__find_queue__(key)

    def __fetch__(self):
        "get the next item from the sequence and queue it up"
        item = next(self.sequence)
        key = self.func(item)
        queue = self.queues.setdefault(key, FetchingQueue(self.__fetch__))
        queue.enqueue(item)

    def __find_queue__(self, key):
        "search for the queue indexed by key"
        try:
            while key not in self.queues:
                self.__fetch__()
            return self.queues[key]
        except StopIteration:
            raise KeyError(key)

    def get_first_n_queues(self, n):
        """
        Run through the sequence until n queues are created and return
        them. If fewer are created, return those plus empty iterables to
        compensate.
        """
        try:
            while len(self.queues) < n:
                self.__fetch__()
        except StopIteration:
            pass
        values = list(self.queues.values())
        missing = n - len(values)
        values.extend(iter([]) for n in range(missing))
        return values


class FetchingQueue(queue.Queue):
    """
    A FIFO Queue that is supplied with a function to inject more into
    the queue if it is empty.

    >>> values = iter(range(10))
    >>> get_value = lambda: globals()['q'].enqueue(next(values))
    >>> q = FetchingQueue(get_value)
    >>> [x for x in q] == list(range(10))
    True

    Note that tuple(q) or list(q) would not have worked above because
    tuple(q) just copies the elements in the list (of which there are
    none).
    """

    def __init__(self, fetcher):
        super().__init__()
        self._fetcher = fetcher

    def __next__(self):
        while self.empty():
            self._fetcher()
        return self.get()

    def __iter__(self):
        while True:
            try:
                yield next(self)
            except StopIteration:
                return

    def enqueue(self, item):
        self.put_nowait(item)


class Count:
    """
    A stop object that will count how many times it's been called and return
    False on the N+1st call.  Useful for use with takewhile.

    >>> tuple(itertools.takewhile(Count(5), range(20)))
    (0, 1, 2, 3, 4)

    >>> print('catch', Count(5))
    catch at most 5

    It's possible to construct a Count with no limit or infinite limit.

    >>> unl_c = Count(None)
    >>> inf_c = Count(float('Inf'))

    Unlimited or limited by infinity are equivalent.

    >>> unl_c == inf_c
    True

    An unlimited counter is useful for wrapping an iterable to get the
    count after it's consumed.

    >>> tuple(itertools.takewhile(unl_c, range(20)))[-3:]
    (17, 18, 19)
    >>> unl_c.count
    20

    If all you need is the count of items, consider :class:`Counter` instead.
    """

    def __init__(self, limit):
        self.count = 0
        self.limit = limit if limit is not None else float('Inf')

    def __call__(self, arg):
        if self.count > self.limit:
            raise ValueError("Should not call count stop more anymore.")
        self.count += 1
        return self.count <= self.limit

    def __str__(self):
        if self.limit:
            return 'at most %d' % self.limit
        else:
            return 'all'

    def __eq__(self, other):
        return vars(self) == vars(other)


class islice:
    """May be applied to an iterable to limit the number of items returned.
    Works similarly to count, except is called only once on an iterable.
    Functionality is identical to islice, except for __str__ and reusability.

    >>> tuple(islice(5).apply(range(20)))
    (0, 1, 2, 3, 4)

    >>> tuple(islice(None).apply(range(20)))
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19)

    >>> print(islice(3, 10))
    items 3 to 9

    >>> print(islice(3, 10, 2))
    every 2nd item from 3 to 9
    """

    def __init__(self, *sliceArgs):
        self.sliceArgs = sliceArgs

    def apply(self, i):
        return itertools.islice(i, *self.sliceArgs)

    def __str__(self):
        if self.sliceArgs == (None,):
            result = 'all'
        else:
            result = self._formatArgs()
        return result

    def _formatArgs(self):
        def slice_range(a_b):
            return '%d to %d' % (a_b[0], a_b[1] - 1)

        if len(self.sliceArgs) == 1:
            result = 'at most %d' % self.sliceArgs
        if len(self.sliceArgs) == 2:
            result = 'items %s' % slice_range(self.sliceArgs)
        if len(self.sliceArgs) == 3:
            ord = inflect.engine().ordinal(self.sliceArgs[2])
            range = slice_range(self.sliceArgs[0:2])
            result = 'every %(ord)s item from %(range)s' % locals()
        return result


class LessThanNBlanks:
    """
    An object that when called will return True until n false elements
    are encountered.

    Can be used with filter or itertools.ifilter, for example:

    >>> import itertools
    >>> sampleData = ['string 1', 'string 2', '', 'string 3', '',
    ...     'string 4', '', '', 'string 5']
    >>> first = itertools.takewhile(LessThanNBlanks(2), sampleData)
    >>> tuple(first)
    ('string 1', 'string 2', '', 'string 3')
    >>> first = itertools.takewhile(LessThanNBlanks(3), sampleData)
    >>> tuple(first)
    ('string 1', 'string 2', '', 'string 3', '', 'string 4')
    """

    def __init__(self, nBlanks):
        self.limit = nBlanks
        self.count = 0

    def __call__(self, arg):
        self.count += not arg
        if self.count > self.limit:
            raise ValueError("Should not call this object anymore.")
        return self.count < self.limit


class LessThanNConsecutiveBlanks:
    """
    An object that when called will return True until n consecutive
    false elements are encountered.

    Can be used with filter or itertools.ifilter, for example:

    >>> import itertools
    >>> sampleData = ['string 1', 'string 2', '', 'string 3', '', 'string 4',
    ...     '', '', 'string 5']
    >>> first = itertools.takewhile(LessThanNConsecutiveBlanks(2), sampleData)
    >>> tuple(first)
    ('string 1', 'string 2', '', 'string 3', '', 'string 4', '')
    """

    def __init__(self, nBlanks):
        self.limit = nBlanks
        self.count = 0
        self.last = False

    def __call__(self, arg):
        self.count += not arg
        if arg:
            self.count = 0
        self.last = operator.truth(arg)
        if self.count > self.limit:
            raise ValueError("Should not call this object anymore.")
        return self.count < self.limit


class splitter:
    """
    object that will split a string with the given arguments for each call.

    >>> s = splitter(',')
    >>> list(s('hello, world, this is your, master calling'))
    ['hello', ' world', ' this is your', ' master calling']
    """

    def __init__(self, sep=None):
        self.sep = sep

    def __call__(self, s):
        lastIndex = 0
        while True:
            nextIndex = s.find(self.sep, lastIndex)
            if nextIndex != -1:
                yield s[lastIndex:nextIndex]
                lastIndex = nextIndex + 1
            else:
                yield s[lastIndex:]
                break


def grouper_nofill_str(n, iterable):
    """
    Take a sequence and break it up into chunks of the specified size.
    The last chunk may be smaller than size.

    This works very similar to grouper_nofill, except
    it works with strings as well.

    >>> tuple(grouper_nofill_str(3, 'foobarbaz'))
    ('foo', 'bar', 'baz')

    You can still use it on non-strings too if you like.

    >>> tuple(grouper_nofill_str(42, []))
    ()

    >>> tuple(grouper_nofill_str(3, list(range(10))))
    ([0, 1, 2], [3, 4, 5], [6, 7, 8], [9])
    """
    res = more_itertools.chunked(iterable, n)
    if isinstance(iterable, str):
        res = (''.join(item) for item in res)
    return res


infinite_call = more_itertools.repeatfunc


def infiniteCall(f, *args):
    warnings.warn("Use infinite_call")
    return infinite_call(functools.partial(f, *args))


class Counter:
    """
    Wrap an iterable in an object that stores the count of items
    that pass through it.

    >>> items = Counter(range(20))
    >>> items.count
    0
    >>> values = list(items)
    >>> items.count
    20
    """

    def __init__(self, i):
        self.count = 0
        self.iter = zip(itertools.count(1), i)

    def __iter__(self):
        return self

    def __next__(self):
        self.count, result = next(self.iter)
        return result


def empty():
    """
    An empty iterator.
    """
    return iter(tuple())


def is_empty(iterable):
    """
    Return whether the iterable is empty or not. Consumes at most one item
    from the iterator to test.

    >>> is_empty(iter(range(0)))
    True
    >>> is_empty(iter(range(1)))
    False
    """
    try:
        next(iter(iterable))
    except StopIteration:
        return True
    return False


class Reusable:
    """
    An iterator that may be reset and reused.

    >>> ri = Reusable(range(3))
    >>> tuple(ri)
    (0, 1, 2)
    >>> next(ri)
    0
    >>> tuple(ri)
    (1, 2)
    >>> next(ri)
    0
    >>> ri.reset()
    >>> tuple(ri)
    (0, 1, 2)
    """

    def __init__(self, iterable):
        self.__saved = iterable
        self.reset()

    def __iter__(self):
        return self

    def reset(self):
        """
        Resets the iterator to the start.

        Any remaining values in the current iteration are discarded.
        """
        self.__iterator, self.__saved = itertools.tee(self.__saved)

    def __next__(self):
        try:
            return next(self.__iterator)
        except StopIteration:
            # we're still going to raise the exception, but first
            #  reset the iterator so it's good for next time
            self.reset()
            raise


def every_other(iterable):
    """
    Yield every other item from the iterable

    >>> ' '.join(every_other('abcdefg'))
    'a c e g'
    """
    items = iter(iterable)
    while True:
        try:
            yield next(items)
            next(items)
        except StopIteration:
            return


def remove_duplicates(iterable, key=None):
    """
    Given an iterable with items that may come in as sequential duplicates,
    remove those duplicates.

    Unlike unique_justseen, this function does not remove triplicates.

    >>> ' '.join(remove_duplicates('abcaabbccaaabbbcccbcbc'))
    'a b c a b c a a b b c c b c b c'
    >>> ' '.join(remove_duplicates('aaaabbbbb'))
    'a a b b b'
    """
    return itertools.chain.from_iterable(
        map(every_other, map(operator.itemgetter(1), itertools.groupby(iterable, key)))
    )


def skip_first(iterable):
    """
    Skip the first element of an iterable

    >>> tuple(skip_first(range(10)))
    (1, 2, 3, 4, 5, 6, 7, 8, 9)
    """
    return itertools.islice(iterable, 1, None)


def peek(iterable):
    """
    Get the next value from an iterable, but also return an iterable
    that will subsequently return that value and the rest of the
    original iterable.

    >>> l = iter([1,2,3])
    >>> val, l = peek(l)
    >>> val
    1
    >>> list(l)
    [1, 2, 3]
    """
    peeker, original = itertools.tee(iterable)
    return next(peeker), original


class Peekable:
    """
    Wrapper for a traditional iterable to give it a peek attribute.

    >>> nums = Peekable(range(2))
    >>> nums.peek()
    0
    >>> nums.peek()
    0
    >>> next(nums)
    0
    >>> nums.peek()
    1
    >>> next(nums)
    1
    >>> nums.peek()
    Traceback (most recent call last):
    ...
    StopIteration

    Peekable should accept an iterable and not just an iterator.

    >>> list(Peekable(range(2)))
    [0, 1]
    """

    def __new__(cls, iterator):
        # if the iterator is already 'peekable', return it; otherwise
        # wrap it
        if hasattr(iterator, 'peek'):
            return iterator
        else:
            return object.__new__(cls)

    def __init__(self, iterator):
        self.iterator = iter(iterator)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.iterator)

    def peek(self):
        result, self.iterator = peek(self.iterator)
        return result


def takewhile_peek(predicate, iterable):
    """
    Like takewhile, but takes a peekable iterable and doesn't
    consume the non-matching item.

    >>> items = Peekable(range(10))
    >>> is_small = lambda n: n < 4

    >>> small_items = takewhile_peek(is_small, items)

    >>> list(small_items)
    [0, 1, 2, 3]

    >>> list(items)
    [4, 5, 6, 7, 8, 9]

    >>> empty = takewhile_peek(is_small, Peekable([]))
    >>> list(empty)
    []

    >>> items = Peekable([3])
    >>> small_items = takewhile_peek(is_small, items)
    >>> list(small_items)
    [3]
    >>> list(items)
    []

    >>> items = Peekable([4])
    >>> small_items = takewhile_peek(is_small, items)
    >>> list(small_items)
    []
    >>> list(items)
    [4]
    """
    while True:
        try:
            if not predicate(iterable.peek()):
                break
            yield next(iterable)
        except StopIteration:
            break


def first(iterable, *args):
    """
    Return the first item from the iterable.

    >>> first(range(11))
    0
    >>> first([3,2,1])
    3
    >>> iter = range(11)
    >>> first(iter)
    0

    Raises StopIteration if no value is present.

    >>> first([])
    Traceback (most recent call last):
    ...
    StopIteration

    Pass a default to be used when iterable is empty.

    >>> first([], None)

    """
    iterable = iter(iterable)
    return next(iterable, *args)


def last(iterable):
    """
    Return the last item from the iterable, discarding the rest.

    >>> last(range(20))
    19
    >>> last([])
    Traceback (most recent call last):
    ...
    ValueError: Iterable contains no items
    """
    for item in iterable:
        pass
    try:
        return item
    except NameError:
        raise ValueError("Iterable contains no items")


def one(item):
    """
    Return the first element from the iterable, but raise an exception
    if elements remain in the iterable after the first.

    >>> one(['val'])
    'val'

    >>> one(['val', 'other'])
    Traceback (most recent call last):
    ...
    ValueError: ...values to unpack...

    >>> one([])
    Traceback (most recent call last):
    ...
    ValueError: ...values to unpack...

    >>> numbers = itertools.count()
    >>> one(numbers)
    Traceback (most recent call last):
    ...
    ValueError: ...values to unpack...
    >>> next(numbers)
    2
    """
    (result,) = item
    return result


def nwise(iter, n):
    """
    Like pairwise, except returns n-tuples of adjacent items.
    s -> (s0,s1,...,sn), (s1,s2,...,s(n+1)), ...
    """
    iterset = [iter]
    while len(iterset) < n:
        iterset[-1:] = itertools.tee(iterset[-1])
        next(iterset[-1], None)
    return zip(*iterset)


def window(iter, pre_size=1, post_size=1):
    """
    Given an iterable, return a new iterable which yields triples of
    (pre, item, post), where pre and post are the items preceeding and
    following the item (or None if no such item is appropriate). pre
    and post will always be pre_size and post_size in length.

    >>> example = window(range(10), pre_size=2)
    >>> pre, item, post = next(example)
    >>> pre
    (None, None)
    >>> post
    (1,)
    >>> next(example)
    ((None, 0), 1, (2,))
    >>> list(example)[-1]
    ((7, 8), 9, (None,))
    """
    pre_iter, iter = itertools.tee(iter)
    pre_iter = itertools.chain((None,) * pre_size, pre_iter)
    pre_iter = nwise(pre_iter, pre_size)
    post_iter, iter = itertools.tee(iter)
    post_iter = itertools.chain(post_iter, (None,) * post_size)
    post_iter = nwise(post_iter, post_size)
    next(post_iter, None)
    return zip(pre_iter, iter, post_iter)


class IterSaver:
    def __init__(self, n, iterable):
        self.n = n
        self.iterable = iterable
        self.buffer = collections.deque()

    def __next__(self):
        while len(self.buffer) <= self.n:
            self.buffer.append(next(self.iterable))
        return self.buffer.popleft()


def partition_items(count, bin_size):
    """
    Given the total number of items, determine the number of items that
    can be added to each bin with a limit on the bin size.

    So if you want to partition 11 items into groups of 3, you'll want
    three of three and one of two.

    >>> partition_items(11, 3)
    [3, 3, 3, 2]

    But if you only have ten items, you'll have two groups of three and
    two of two.

    >>> partition_items(10, 3)
    [3, 3, 2, 2]
    """
    num_bins = int(math.ceil(count / float(bin_size)))
    bins = [0] * num_bins
    for i in range(count):
        bins[i % num_bins] += 1
    return bins


def balanced_rows(n, iterable, fillvalue=None):
    """
    Like grouper, but balance the rows to minimize fill per row.
    balanced_rows(3, 'ABCDEFG', 'x') --> ABC DEx FGx"
    """
    iterable, iterable_copy = itertools.tee(iterable)
    count = len(tuple(iterable_copy))
    for allocation in partition_items(count, n):
        row = itertools.islice(iterable, allocation)
        if allocation < n:
            row = itertools.chain(row, [fillvalue])
        yield tuple(row)


def reverse_lists(lists):
    """
    >>> reverse_lists([[1,2,3], [4,5,6]])
    [[3, 2, 1], [6, 5, 4]]
    """

    return list(map(list, map(reversed, lists)))


def always_iterable(item):
    """
    Given an object, always return an iterable. If the item is not
    already iterable, return a tuple containing only the item. If item is
    None, an empty iterable is returned.

    >>> always_iterable([1,2,3])
    <list_iterator...>
    >>> always_iterable('foo')
    <tuple_iterator...>
    >>> always_iterable(None)
    <tuple_iterator...>
    >>> always_iterable(range(10))
    <range_iterator...>
    >>> def _test_func(): yield "I'm iterable"
    >>> print(next(always_iterable(_test_func())))
    I'm iterable

    Although mappings are iterable, treat each like a singleton, as
    it's more like an object than a sequence.

    >>> next(always_iterable(dict(a=1)))
    {'a': 1}
    """
    base_types = str, bytes, collections.abc.Mapping
    return more_itertools.always_iterable(item, base_type=base_types)


def suppress_exceptions(callables, *exceptions):
    """
    Call each callable in callables, suppressing any exceptions supplied. If
    no exception classes are supplied, all Exceptions will be suppressed.

    >>> import functools
    >>> c1 = functools.partial(int, 'a')
    >>> c2 = functools.partial(int, '10')
    >>> list(suppress_exceptions((c1, c2)))
    [10]
    >>> list(suppress_exceptions((c1, c2), KeyError))
    Traceback (most recent call last):
    ...
    ValueError: invalid literal for int() with base 10: 'a'
    """
    if not exceptions:
        exceptions = (Exception,)
    for callable in callables:
        try:
            yield callable()
        except exceptions:
            pass


def apply(func, iterable):
    """
    Like 'map', invoking func on each item in the iterable,
    except return the original item and not the return
    value from the function.

    Useful when the side-effect of the func is what's desired.

    >>> res = apply(print, range(1, 4))
    >>> list(res)
    1
    2
    3
    [1, 2, 3]
    """
    for item in iterable:
        func(item)
        yield item


def list_or_single(iterable):
    """
    Given an iterable, return the items as a list. If the iterable contains
    exactly one item, return that item. Correlary function to always_iterable.
    """
    warnings.warn("Use maybe_single", DeprecationWarning, stacklevel=2)
    return maybe_single(list(iterable))


def maybe_single(sequence):
    """
    Given a sequence, if it contains exactly one item,
    return that item, otherwise return the sequence.
    Correlary function to always_iterable.

    >>> maybe_single(tuple('abcd'))
    ('a', 'b', 'c', 'd')
    >>> maybe_single(['a'])
    'a'
    """
    try:
        (single,) = sequence
    except ValueError:
        return sequence
    return single


def self_product(iterable):
    """
    Return the cross product of the iterable with itself.

    >>> list(self_product([1, 2, 3]))
    [(1, 1), (1, 2), ..., (3, 3)]
    """
    return itertools.product(*itertools.tee(iterable))


def duplicates(*iterables, **kwargs):
    """
    Yield duplicate items from any number of sorted iterables of items

    >>> items_a = [1, 2, 3]
    >>> items_b = [0, 3, 4, 5, 6]
    >>> list(duplicates(items_a, items_b))
    [(3, 3)]

    It won't behave as you expect if the iterables aren't ordered

    >>> items_b.append(1)
    >>> list(duplicates(items_a, items_b))
    [(3, 3)]
    >>> list(duplicates(items_a, sorted(items_b)))
    [(1, 1), (3, 3)]

    This function is most interesting when it's operating on a key
    of more complex objects.

    >>> items_a = [dict(email='joe@example.com', id=1)]
    >>> items_b = [dict(email='joe@example.com', id=2), dict(email='other')]
    >>> dupe, = duplicates(items_a, items_b, key=operator.itemgetter('email'))
    >>> dupe[0]['email'] == dupe[1]['email'] == 'joe@example.com'
    True
    >>> dupe[0]['id']
    1
    >>> dupe[1]['id']
    2
    """
    key = kwargs.pop('key', lambda x: x)
    assert not kwargs
    zipped = heapq.merge(*iterables, key=key)
    grouped = itertools.groupby(zipped, key=key)
    groups = (tuple(g) for k, g in grouped)

    def has_dupes(group):
        return len(group) > 1

    return filter(has_dupes, groups)


def assert_ordered(iterable, key=lambda x: x, comp=operator.le):
    """
    Assert that for all items in the iterable, they're in order based on comp

    >>> list(assert_ordered(range(5)))
    [0, 1, 2, 3, 4]
    >>> list(assert_ordered(range(5), comp=operator.ge))
    Traceback (most recent call last):
    ...
    AssertionError: 0 < 1
    >>> list(assert_ordered(range(5, 0, -1), key=operator.neg))
    [5, 4, 3, 2, 1]
    """
    err_tmpl = (
        "{pair[0]} > {pair[1]}"
        if comp is operator.le
        else "{pair[0]} < {pair[1]}"
        if comp is operator.ge
        else "not {comp} {pair}"
    )
    for pair in more_itertools.pairwise(iterable):
        keyed = tuple(map(key, pair))
        # cannot use bare assert due to jaraco/jaraco.test#3
        if not comp(*keyed):
            raise AssertionError(err_tmpl.format(**locals()))
        yield pair[0]
    yield pair[1]


def collate_revs(old, new, key=lambda x: x, merge=lambda old, new: new):
    """
    Given revision sets old and new, each containing a series
    of revisions of some set of objects, collate them based on
    these rules:

    - all items from each set are yielded in stable order
    - items in old are yielded first
    - items in new are yielded last
    - items that match are yielded in the order in which they
      appear, giving preference to new

    Items match based on the 'key' parameter (identity by default).

    Items are merged using the 'merge' function, which accepts the old
    and new items to be merged (returning new by default).

    This algorithm requires fully materializing both old and new in memory.

    >>> rev1 = ['a', 'b', 'c']
    >>> rev2 = ['a', 'd', 'c']
    >>> result = list(collate_revs(rev1, rev2))

    'd' must appear before 'c'
    >>> result.index('d') < result.index('c')
    True

    'b' must appear before 'd' because it came chronologically
    first.
    >>> result.index('b') < result.index('d')
    True

    >>> result
    ['a', 'b', 'd', 'c']

    >>> list(collate_revs(['a', 'b', 'c'], ['d']))
    ['a', 'b', 'c', 'd']

    >>> list(collate_revs(['b', 'a'], ['a', 'b']))
    ['a', 'b']

    >>> list(collate_revs(['a', 'c'], ['a', 'b', 'c']))
    ['a', 'b', 'c']

    Given two sequences of things out of order, regardless
    of which order in which the items are merged, all
    keys should always be merged.

    >>> from more_itertools import consume
    >>> left_items = ['a', 'b', 'c']
    >>> right_items = ['a', 'c', 'b']
    >>> consume(collate_revs(left_items, right_items, merge=print))
    a a
    c c
    b b
    >>> consume(collate_revs(right_items, left_items, merge=print))
    a a
    b b
    c c

    The merge should not suppress non-True items:

    >>> consume(collate_revs([0, 1, 2, None, ''], [0, None, ''], merge=print))
    None None
    <BLANKLINE>
    0 0

    """
    missing = object()

    def maybe_merge(*items):
        """
        Merge any non-null items
        """

        def not_missing(ob):
            return ob is not missing

        return functools.reduce(merge, filter(not_missing, items))

    new_items = collections.OrderedDict((key(el), el) for el in new)
    old_items = collections.OrderedDict((key(el), el) for el in old)

    # use the old_items as a reference
    for old_key, old_item in _mutable_iter(old_items):
        if old_key not in new_items:
            yield old_item
            continue

        # yield all new items that appear before the matching key
        before, match_new, new_items = _swap_on_miss(partition_dict(new_items, old_key))
        for new_key, new_item in before.items():
            # ensure any new keys are merged with previous items if
            # they exist
            yield maybe_merge(new_item, old_items.pop(new_key, missing))
        yield merge(old_item, match_new)

    # finally, yield whatever is leftover
    # yield from new_items.values()
    for item in new_items.values():
        yield item


def _mutable_iter(dict):
    """
    Iterate over items in the dict, yielding the first one, but allowing
    it to be mutated during the process.
    >>> d = dict(a=1)
    >>> it = _mutable_iter(d)
    >>> next(it)
    ('a', 1)
    >>> d
    {}
    >>> d.update(b=2)
    >>> list(it)
    [('b', 2)]
    """
    while dict:
        prev_key = next(iter(dict))
        yield prev_key, dict.pop(prev_key)


def _swap_on_miss(partition_result):
    """
    Given a partition_dict result, if the partition missed, swap
    the before and after.
    """
    before, item, after = partition_result
    return (before, item, after) if item else (after, item, before)


def partition_dict(items, key):
    """
    Given an ordered dictionary of items and a key in that dict,
    return an ordered dict of items before, the keyed item, and
    an ordered dict of items after.

    >>> od = collections.OrderedDict(zip(range(5), 'abcde'))
    >>> before, item, after = partition_dict(od, 3)
    >>> before
    OrderedDict([(0, 'a'), (1, 'b'), (2, 'c')])
    >>> item
    'd'
    >>> after
    OrderedDict([(4, 'e')])

    Like string.partition, if the key is not found in the items,
    the before will contain all items, item will be None, and
    after will be an empty iterable.

    >>> before, item, after = partition_dict(od, -1)
    >>> before
    OrderedDict([(0, 'a'), ..., (4, 'e')])
    >>> item
    >>> list(after)
    []
    """

    def unmatched(pair):
        test_key, item = pair
        return test_key != key

    items_iter = iter(items.items())
    item = items.get(key)
    left = collections.OrderedDict(itertools.takewhile(unmatched, items_iter))
    right = collections.OrderedDict(items_iter)
    return left, item, right
