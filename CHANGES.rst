v6.0.1
======

Switch to PEP 420 for namespace package.

v6.0.0
======

Remove ``Counter.GetCount``.
Remove ``flatten`` and ``iflatten``.

v5.0.0
======

``infinite_call`` is superseded by ``more_itertools.repeatfunc``.

Require Python 3.6 or later.

4.4.2
=====

Fixed RuntimeError in takewhile_peek on later Pythons where
StopIteration is no longer allowed in a generator.

4.4.1
=====

Fixed issue in ``collate_revs`` when objects being merged were
non-True.

4.4
===

Add ``collate_revs`` and ``partition_dict``.

4.3
===

Nicer error message in ``assert_ordered`` when the assertion
fails. Now reports the full supplied items and not just the keys
in the errors. When ``<`` or ``>`` are used, the error message
renders more directly.

4.2
===

The ``duplicates`` function now takes an arbitrary number of iterables.

Added ``assert_ordered`` function.

4.1
===

Added ``duplicates`` function.

4.0.0
=====

Switch to `pkgutil namespace technique
<https://packaging.python.org/guides/packaging-namespace-packages/#pkgutil-style-namespace-packages>`_
for the ``jaraco`` namespace.

3.0.0
=====

* Refreshed project metadata, now built using declarative
  config. Installation from sdist now requries setuptools
  34.4.

2.5.2
=====

* Fix deprecation warning in ``always_iterable``.
* Leverage base_type parameter in
  ``more_itertools.always_iterable``.

2.5.1
=====

* Set stacklevel in deprecated functions for better
  visibility of the call.

2.5
===

* Added new ``maybe_single`` function.
* Deprecated ``list_or_iterable`` in favor of
  ``maybe_single``.

2.4
===

* Deprecated ``flatten`` and ``iflatten`` in favor of
  ``more_itertools.collapse``. Deprecated
  ``iterable_test``, only used by deprecated functions.

* Bump dependency on more_itertools 4.0.0.

2.3
===

* Added ``self_product``.

2.2
===

* ``first`` now accepts a default value, same as ``next``.

2.1.1
=====

* #3: Fix failures on Python 3.7 due to the introduction of
  PEP 479.

2.1
===

* Use ``more_itertools.more.always_iterable`` in place
  of ``always_iterable`` except when a mapping is
  included.

2.0.1
=====

* Refresh package.

2.0
===

* In ``always_iterable``, mappings are now considered
  singletons. It seems that the way ``always_iterable``
  is generally used, one wouldn't expect to only iterate
  on a mapping, but there are cases where a dictionary
  should behave like a singleton object.

1.8
===

* Deprecated ``infiniteCall`` and replaced it with
  ``infinite_call`` which only takes a single argument
  (the function to call).

1.7.1
=====

* Fix failing tests on Python 2.

1.7
===

* Moved hosting to github.

1.6
===

* Releases now include wheels.

1.5
===

* Add ``takewhile_peek`` function.

1.4
===

* Add ``list_or_single`` function.

1.3
===

* Add ``apply`` to apply a function to an iterable, but yield the
  original items.

1.1
===

* Update ``Count`` object to support comparison for equality and accept
  None to mean explicitly Infinity. See the docs for details.
* Fixed Python 3 issues on ``Counter`` object. Added docstrings.
* Added ``Counter.count`` attribute.
* ``Counter.GetCount`` is now deprecated. Use ``.count`` instead.

1.0
===

Initial release based on jaraco.util 10.7.
