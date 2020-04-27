import sys


def pytest_collection_modifyitems(session, config, items):
    remove_broken_tests(items)


def remove_broken_tests(items):
    # Remove broken tests for PyPy3
    if hasattr(sys, 'pypy_version_info'):
        broken_test_names = ['jaraco.itertools.always_iterable']
        items[:] = (item for item in items if item.name not in broken_test_names)
