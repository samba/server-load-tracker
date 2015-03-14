import unittest
import sys

from ServerTrack import stats

class StatsHandlerTest(unittest.TestCase):


	def testSearch(self):

		data = stats.StatsCollector(max_duration = 500)

		# Range 0 to 50, increments of 1
		for i in xrange(1, 50, 3):
			data.push(value = i, timestamp = i)

		self.assertEqual(data.find_preceding_entry_index(0), -1) # not found
		self.assertEqual(data.find_preceding_entry_index(25), 8)
		self.assertEqual(data.find_preceding_entry_index(26), 8)
		self.assertEqual(data.find_preceding_entry_index(27), 8)
		self.assertEqual(data.find_preceding_entry_index(29), 9)

	def testTruncate(self):
		data = stats.StatsCollector(max_duration = 2000)

		# This produces a range from [1 to 2991].
		for i in xrange(1, 3000, 10):
			data.push(value = i, timestamp = i)

		# Since we're simulating a timestamp of "2991" above, with a max_duration of "2000",
		# all values less than 991 [i.e. 2991 less 2000] are removed, as the binary search
		# model will preserve the value matching the "earliest" (i.e. 991).
		self.assertEqual(len(data.history), 201)


	def testQuery(self):
		data = stats.StatsCollector(max_duration = 2000)

		# This produces a range from [1 to 3000].
		for i in xrange(1, 3000, 1):
			data.push(value = i, timestamp = i)

		results = list(data.query(2950))
		self.assertEqual(len(results), 50)

	def testRepeatedTimeIndex(self):
		data = stats.StatsCollector(max_duration = 50)

		data.push(timestamp = 7, value = 1)
		data.push(timestamp = 8, value = 1)
		data.push(timestamp = 10, value = 1) # duplicate
		data.push(timestamp = 10, value = 1) # duplicate
		data.push(timestamp = 11, value = 1)

		self.assertEqual(len(list(data.query(10))), 3)
		self.assertEqual(len(list(data.query(9))), 4) # because it includes #8
		self.assertEqual(len(list(data.query(8))), 4)


	def testSelection(self):
		data = stats.StatsCollector(max_duration = 50)
		data.push(name = 'a', timestamp = 1, value = 8)
		data.push(name = 'b', timestamp = 2, value = 7)
		data.push(name = 'a', timestamp = 3, value = 6)
		data.push(name = 'a', timestamp = 4, value = 5)
		data.push(name = 'a', timestamp = 5, value = 4)
		data.push(name = 'a', timestamp = 6, value = 3)
		data.push(name = 'b', timestamp = 7, value = 2)
		data.push(name = 'a', timestamp = 8, value = 1)
		data.push(name = 'a', timestamp = 9, value = 100)
		data.push(name = 'a', timestamp = 10, value = 101)
		data.push(name = 'b', timestamp = 11, value = 102)
		data.push(name = 'b', timestamp = 12, value = 103)
		data.push(name = 'b', timestamp = 13, value = 104)
		data.push(name = 'a', timestamp = 14, value = 105)
		data.push(name = 'a', timestamp = 15, value = 106)

		results_a = list(data.query(1, name = 'a'))
		results_b = list(data.query(1, name = 'b'))
		
		self.assertEqual(len(results_a), 10)
		self.assertEqual(len(results_b), 5)




