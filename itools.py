# -*- coding: UTF-8 -*-

"""itools
	Tools for working with iterables.  Complements itertools.
	
Copyright © 2004 Sandia National Laboratories  
"""

__author__ = 'Jason R. Coombs <jaraco@sandia.gov>'
__version__ = '$Revision: 8 $a'[11:-2]
__svnauthor__ = '$Author: Jaraco $'[9:-2]
__date__ = '$Date: 9-12-04 12:51 $'[7:-2]

import operator, itertools
from tools import ordinalth

class Count( object ):
	"""
	A stop object that will count how many times it's been called and return
	False on the N+1st call.  Useful for use with takewhile.
	>>> tuple( itertools.takewhile( Count( 5 ), xrange( 20 ) ) )
	(0, 1, 2, 3, 4)
	"""
	def __init__( self, limit ):
		self.count = 0
		self.limit = limit
		
	def __call__( self, arg ):
		if not self.limit:
			result = True
		else:
			if self.count > self.limit:
				raise ValueError, "Should not call count stop more anymore."
			result = self.count < self.limit
		self.count += 1
		return result

	def __str__( self ):
		if limit:
			return 'at most %d' % limit
		else:
			return 'all'

class islice( object ):
	"""May be applied to an iterable to limit the number of items returned.
	Works similarly to count, except is called only once on an iterable.
	Functionality is identical to islice, except for __str__ and reusability.
	>>> tuple( islice( 5 ).apply( xrange( 20 ) ) )
	(0, 1, 2, 3, 4)
	>>> tuple( islice( None ).apply( xrange( 20 ) ) )
	(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19)
	"""
	def __init__( self, *sliceArgs ):
		self.sliceArgs = sliceArgs

	def apply( self, i ):
		return itertools.islice( i, *self.sliceArgs )

	def __str__( self ):
		if self.sliceArgs == ( None, ):
			result = 'all'
		else:
			result = self._formatArgs()
		return result

	def _formatArgs( self ):
		baseOneRange = lambda (a,b): '%d to %d' % (a+1,b)
		if len( self.sliceArgs ) == 1:
			result = 'at most %d' % self.sliceArgs
		if len( self.sliceArgs ) == 2:
			result = 'items %s' % baseOneRange( self.sliceArgs )
		if len( self.sliceArgs ) == 3:
			result = 'every %s item from %s' % ( ordinalth( self.sliceArgs[2] ), baseOneRange( self.sliceArgs[0:2] ) )
		return result
	
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

def adjacentPairs( i ):
	"""Yield adjacent pairs of a single iterable as pairs
	>>> tuple( adjacentPairs( iter( xrange( 5 ) ) )
	((0, 1), (1, 2), (2, 3), (3, 4))
	"""
	last = i.next()
	while True:
		next = i.next()
		yield ( last, next )
		last = next

def chain( sequences ):
	"""functions like itertools.chain, except chains everything in sequences.
	Equivalent to itertools.chain( *sequences ) except sequences is evaluated
	on demand."""
	for sequence in sequences:
		for item in sequence:
			yield item

def infiniteCall( f, *args ):
	"Perpetually yield the result of calling function f."
	while True:
		yield f( *args )

def evalAll( i ):
	"Cause an iterable to evaluate all of its arguments, but don't store any result."
	for x in i: pass

def evalN( i, n ):
	"Cause an iterable to evaluate n of its arguments, but don't store any result."
	for x in itertools.islice( i, n ): pass
	
class Counter( object ):
	def __init__( self, i ):
		self.__count__ = 0
		self.__i__ = enumerate( i )

	def __iter__( self ): return self

	def next( self ):
		index, result = self.__i__.next()
		self.__count__ = index + 1
		return result

	def GetCount( self ):
		return self.__count__