# -*- coding: UTF-8 -*-

"""
jaraco.itertools
Tools for working with iterables.  Complements itertools and more_itertools.
"""

from __future__ import absolute_import, unicode_literals, print_function

import operator
import itertools
import collections
import math
import warnings
import functools

try:
	import collections.abc
except ImportError:
	collections.abc = collections

import six
from six.moves import queue, xrange as range

import inflect
from more_itertools import more
from more_itertools import recipes


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
	result = recipes.grouper(num_rows, seq)
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


class GroupbySaved(object):
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
		if six.PY3:
			super(FetchingQueue, self).__init__()
		else:
			queue.Queue.__init__(self)
		self._fetcher = fetcher

	def __next__(self):
		while self.empty():
			self._fetcher()
		return self.get()
	next = __next__

	def __iter__(self):
		while True:
			try:
				yield next(self)
			except StopIteration:
				return

	def enqueue(self, item):
		self.put_nowait(item)


class Count(object):
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


class islice(object):
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


class LessThanNBlanks(object):
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


class LessThanNConsecutiveBlanks(object):
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


class splitter(object):
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
	res = more.chunked(iterable, n)
	if isinstance(iterable, six.string_types):
		res = (''.join(item) for item in res)
	return res


def infinite_call(f):
	"""
	Perpetually yield the result of calling function f.

	>>> counter = itertools.count()
	>>> get_next = functools.partial(next, counter)
	>>> numbers = infinite_call(get_next)
	>>> next(numbers)
	0
	>>> next(numbers)
	1
	"""
	return (f() for _ in itertools.repeat(None))


def infiniteCall(f, *args):
	warnings.warn("Use infinite_call")
	return infinite_call(functools.partial(f, *args))


class Counter(object):
	"""
	Wrap an iterable in an object that stores the count of items
	that pass through it.

	>>> items = Counter(range(20))
	>>> values = list(items)
	>>> items.count
	20
	"""

	def __init__(self, i):
		self.count = 0
		self._orig_iter = iter(i)

	def __iter__(self):
		return self

	def __next__(self):
		result = next(self._orig_iter)
		self.count += 1
		return result
	next = __next__

	def GetCount(self):
		warnings.warn(
			"Use count attribute directly", DeprecationWarning,
			stacklevel=2)
		return self.count

# todo, factor out caching capability


class iterable_test(dict):
	def __init__(self, ignore_classes=six.string_types + (six.binary_type,)):
		"""ignore_classes must include str, because if a string
		is iterable, so is a single character, and the routine runs
		into an infinite recursion"""
		warnings.warn(
			"Slated for removal", DeprecationWarning, stacklevel=2)
		assert set(six.string_types) <= set(ignore_classes), (
			'str must be in ignore_classes')
		self.ignore_classes = ignore_classes

	def __getitem__(self, candidate):
		return dict.get(self, type(candidate)) or self._test(candidate)

	def _test(self, candidate):
		try:
			if isinstance(candidate, tuple(self.ignore_classes)):
				raise TypeError
			iter(candidate)
			result = True
		except TypeError:
			result = False
		self[type(candidate)] = result
		return result


def iflatten(subject, test=None):
	if test is None:
		test = iterable_test()
	if not test[subject]:
		yield subject
	else:
		for elem in subject:
			for subelem in iflatten(elem, test):
				yield subelem


def flatten(subject, test=None):
	"""
	*Deprecated*: Use more_itertools.collapse instead.
	"""
	warnings.warn(
		"Use more_itertools.collapse instead",
		DeprecationWarning,
		stacklevel=2)
	return list(more.collapse(subject, base_type=(bytes,)))


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


class Reusable(object):
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
	next = __next__


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
	return itertools.chain.from_iterable(six.moves.map(
		every_other, six.moves.map(
			operator.itemgetter(1),
			itertools.groupby(iterable, key)
		)))


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


class Peekable(object):
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
	next = __next__

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
	"""
	while True:
		if not predicate(iterable.peek()):
			break
		yield next(iterable)


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
	result, = item
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
	return six.moves.zip(*iterset)


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
	return six.moves.zip(pre_iter, iter, post_iter)


class IterSaver(object):
	def __init__(self, n, iterable):
		self.n = n
		self.iterable = iterable
		self.buffer = collections.deque()

	def __next__(self):
		while len(self.buffer) <= self.n:
			self.buffer.append(next(self.iterable))
		return self.buffer.popleft()
	next = __next__


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
	base_types = six.text_type, bytes, collections.abc.Mapping
	return more.always_iterable(item, base_type=base_types)


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
		exceptions = Exception,
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
		single, = sequence
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
