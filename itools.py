import operator

class Count( object ):
	"""
	A stop object that will count how many times it's been called and return
	False on the Nth call.
	"""
	def __init__( self, limit ):
		self.count = 0
		self.limit = limit
		
	def __call__( self, arg ):
		self.count += 1
		if self.count > self.limit:
			raise ValueError, "Should not call count stop more anymore."
		return self.count < self.limit

class LessThanNBlanks( object ):
	"""
	An object that when called will return True until n false elements
	are encountered.

	Can be used with filter or itertools.ifilter, for example:

>>> import itertools
>>> sampleData = ['string 1', 'string 2', '', 'string 3', '', 'string 4', '', '', 'string 5' ]
>>> first = itertools.takewhile( itools.LessThanNBlanks( 2 ), sampleData )
>>> tuple( first )
('string 1', 'string 2', '', 'string 3')
>>> first = itertools.takewhile( itools.LessThanNBlanks( 3 ), sampleData )
>>> tuple( first )
('string 1', 'string 2', '', 'string 3', '', 'string 4')
	"""
	def __init__( self, nBlanks ):
		self.limit = nBlanks
		self.count = 0

	def __call__( self, arg ):
		self.count += not arg
		if self.count > self.limit:
			raise ValueError, "Should not call this object anymore."
		return self.count < self.limit

class LessThanNConsecutiveBlanks( object ):
	"""
	An object that when called will return True until n consecutive
	false elements are encountered.

	Can be used with filter or itertools.ifilter, for example:

>>> import itertools
>>> sampleData = ['string 1', 'string 2', '', 'string 3', '', 'string 4', '', '', 'string 5' ]
>>> first = itertools.takewhile( itools.LessThanNConsecutiveBlanks( 2 ), sampleData )
>>> tuple( first )
('string 1', 'string 2', '', 'string 3', '', 'string 4', '')
	"""
	
	def __init__( self, nBlanks ):
		self.limit = nBlanks
		self.count = 0
		self.last = False
		
	def __call__( self, arg ):
		self.count += not arg
		if arg:
			self.count = 0
		self.last = operator.truth( arg )
		if self.count > self.limit:
			raise ValueError, "Should not call this object anymore."
		return self.count < self.limit
