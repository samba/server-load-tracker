import time
import datetime
import logging


class StatsCollector(object):

	def __init__(self, max_duration = 3600 * 24):
		self.max_duration = max_duration
		self.history = []

	def truncate(self, earliest):
		preceding = self.find_preceding_entry_index(earliest)
		if preceding > 0:
			del self.history[0:preceding] # Truncate history

	def push(self, timestamp = None, **kwargs):
		"""Add a record to the set and truncate any expired history"""
		if timestamp is None:
			timestamp = time.time()
		self.history.append((timestamp, kwargs))

		# TODO: possible optimization: for practical purposes we may be able to
		# truncate on some frequency, possibly pseudorandomly triggered, rather
		# than on every insert. Reporting shouldn't be sensitive to the presence
		# of expired data, so it'd be important only for total memory usage.
		self.truncate(timestamp - self.max_duration)

	def find_preceding_entry_index(self, earliest):
		"""This is a rather oblique binary search approach to reduce the cost of age-based queries
		   on the time-series. Returns the index in the history that precedes (or equals) the 
		   given |earliest| time value. """

		total = len(self.history)
		current = total >> 1 # start at midpoint (total / 2)

		if total and (earliest > self.history[total -1][0]):
			raise IndexError, "The given time index exceeds history's upper limit"

		if total and (earliest < self.history[0][0]):
			return -1

		# Rewind at half-steps through history
		while ((current > 1) and (earliest < self.history[current][0])):
			current = current >> 1

		# Step forward until we find a later entry
		step = (current >> 1)
		while (step and current and (earliest > self.history[current][0])):
			current = current + step
			step = step >> 1
			
		# Rewind (again) to find the first matching entry
		while (current and (earliest < self.history[current][0])):
			current = current -1

		return current # maybe 0

	def query(self, earliest, **filter_param):
		"""Extract a set from the collected data, based on age.
			Optional filtering of the results based on matching properties
			within the related values of each record.

			Parameters (required): 
			 - int(earliest): the maximum age of results to produce

			Keyword arguments are applied as filter definition to match
			the record properties.

		"""
		try:
			index = self.find_preceding_entry_index(earliest)
		except IndexError, e:
			return # empty set
		
		def _match(item):
			for key, val in filter_param.iteritems():
				if item[1].get(key, None) != val:
					return False
			return True

		# Generator here, so invoking methods can terminate it efficiently
		# simply by breaking out of their own loops.
		while index < len(self.history):
			if _match(self.history[index]):
				yield self.history[index]
			index = index + 1



def tagRecordsByTimeBasis(records, time_basis):
	for time, values in sorted(records, key = lambda rec: rec[0]):
		yield int(time / time_basis), time, values


def groupRecordsByTimeBasis(records, time_basis):
	"""Segment a data set by time groups; i.e. for grouping by minute, etc.

	   Parameters
	   	- records: the iterable representing each record, (int(timestamp), values)
	   	- time_basis: the number of seconds for each group to aggregate

	   Yields:
	   	- timestamp
	   	- list of related records (values)

	   """
	current_id, current_set = None, []

	def render_timestamp(current_id):
		dt = datetime.datetime.fromtimestamp(current_id * time_basis)
		return dt.strftime('%Y-%m-%dT%H:%M:%S')



	for tag, timestamp, values in tagRecordsByTimeBasis(records, time_basis):
		if current_id is None:
			# Starting fresh
			current_id = tag
			current_set.append(values)
		elif current_id == tag:
			# Sequence continues
			current_set.append(values)
		else:
			# A tag change occured; emit current set
			yield render_timestamp(current_id), current_set
			# Start the next sequence
			current_id = tag
			current_set = [ values ]

	# There may be a residual set for the last tag
	if current_id is not None and len(current_set):
		yield render_timestamp(current_id), current_set



