import operator, itertools

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

class splitter( object ):
	"""object that will split a string with the given arguments for each call
	>>> s = splitter( ',' )
	>>> list( s( 'hello, world, this is your, master calling' ) )
	['hello', ' world', ' this is your', ' master calling']
"""
	def __init__( self, sep = None ):
		self.sep = sep

	def __call__( self, s ):
		lastIndex = 0
		while True:
			nextIndex = s.find( self.sep, lastIndex )
			if nextIndex != -1:
				yield s[ lastIndex:nextIndex ]
				lastIndex = nextIndex + 1
			else:
				yield s[ lastIndex: ]
				break

def chunkGenerator( seq, size ):
	"""returns sequence or iterable seq in chunks of size
	>>> c = chunkGenerator( xrange( 11 ), 3 )
	>>> tuple( c )
	((0, 1, 2), (3, 4, 5), (6, 7, 8), (9, 10))
	>>> c = chunkGenerator( range( 10 ), 3 )
	>>> tuple( c )
	((0, 1, 2), (3, 4, 5), (6, 7, 8), (9,))
	"""
	if isinstance( seq, basestring ):
		raise TypeError, 'Cannot use itools.chunkGenerator on strings.  Use tools.chunkGenerator instead'
	# make sure sequence is iterable
	seq = iter( seq )
	while 1:
		result = tuple( itertools.islice( seq, size ) )
		if not result: break
		yield result
