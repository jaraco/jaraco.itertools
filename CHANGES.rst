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
