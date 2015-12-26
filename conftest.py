import six


def pytest_collection_modifyitems(session, config, items):
	remove_PY2_broken_tests(items)


def remove_PY2_broken_tests(items):
	if six.PY3:
		return
	broken_test_names = [
		'jaraco.itertools.always_iterable',
		'jaraco.itertools.flatten',
	]
	items[:] = (
		item
		for item in items
		if item.name not in broken_test_names
	)
