
from gevent import monkey
monkey.patch_all()

from gevent.pool import Pool
from gevent.wsgi import WSGIServer
from gevent.queue import Queue
from gevent import spawn

import gevent
import signal
import json
import urlparse
import time
import re

from stats import StatsCollector, groupRecordsByTimeBasis

class ServerTrack(object):
	"""A tracker service class; each instance acts as its own service manager, and can listen on a dedicated port.

		Options:
			- pool_size: threads allocated through gevent for handlings concurrent requests
			- max_history_duration: *seconds* of history to be retained (each time a record is added)
			- service_port: which TCP port to listen on

		The history retention cycle is maintained through the StatsCollector class of the |stats| module. 

	"""


	RE_URI_PARSE = re.compile(r'^/perf/([A-Za-z0-9]{2,128})/(last_hour|last_day|last_minute)?')

	REPORT_MODES = {
		'last_minute': (60, 1), # duration 60 seconds, interval 1 second
		'last_hour': (3600, 60), # duration 60 minutes, interval 1 minute
		'last_day': (24 * 3600, 3600) # duration 24 hours, interval 60 minutes
	}

	def __init__(self, pool_size = 5, max_history_duration = 3600 * 24, service_port = 8080):
		self.server = None
		self.service_port = service_port
		self.max_history_duration = int(max_history_duration) # seconds
		self.pool = Pool(pool_size)


	@staticmethod
	def assemble_stats(collector, server_name, now, duration, interval):
		"""Generate a list of records for a server (by name), aggregating time intervals for the given duration,
		   relative to a particular starting time (i.e. now)"""
		query = collector.query(duration, hostname = server_name)
		for time_id, records in groupRecordsByTimeBasis(query, interval):
			cpuload = sum([ rec.get('cpuload') for rec in records ])
			memload = sum([ rec.get('memload') for rec in records ])
			yield {
				'time': time_id,
				'cpuload': cpuload / len(records),
				'memload': memload / len(records),
				'samples': len(records),
				'interval': interval
			}


	def run(self):
		"""Prepare the WSGI service layer. [Refactor for clarity in progress]."""

		collector = StatsCollector(max_duration = self.max_history_duration)

		def retrieve_stats(start_response, server_name, stats_mode):
			"""Constructs a JSON response from aggregated data; responds to compliant GET requests."""
			if stats_mode in self.REPORT_MODES:
				duration, interval = self.REPORT_MODES[stats_mode]
			else:
				start_response('400 Bad Request', [])
				return []

			now = time.time()
			stats = self.assemble_stats(collector, server_name, now, duration, interval)
			start_response('200 OK', [('Content-Type', 'application/json')])
			return [ json.dumps([ i for i in stats ]) ]
	

		def post_stats(start_response, server_name, req_body):
			"""Append a record to the history collector; Responds to compliant POST requests."""
			if req_body is not None:
				params = urlparse.parse_qs(req_body.read())
				collector.push(
					timestmap = time.time(),
					hostname = server_name,
					cpuload = float(params.get('cpuload', [])[0]),
					memload = float(params.get('memload', [])[0])
				)

				start_response('201 Created', [])
				return []
			else:
				start_response('400 Bad Request', [])


		def listener(env, start_response):
			"""Main WSGI responder; gevent wraps this in a greenlet."""
			method = env.get('REQUEST_METHOD')
			uri = env.get('SCRIPT_NAME', '') + env.get('PATH_INFO', '')
			req = self.RE_URI_PARSE.match(uri)

			if method == 'GET':
				if req is not None: # Compliant GET request
					return retrieve_stats(start_response, req.group(1), req.group(2))
				else: # Erroneous request
					start_response('404 Not Found', [])
					return []
			if method == 'POST':
				if req is not None: # Compliant POST request
					return post_stats(start_response, req.group(1), env.get('wsgi.input', None))
				else: # Erroneous request
					start_response('404 Not Found', [])
					return []


		# Start the service
		gevent.signal(signal.SIGQUIT, gevent.kill)
		gevent.signal(signal.SIGINT, self.stop)
		self.server = WSGIServer(('', self.service_port), listener, spawn = self.pool)
		self.server.serve_forever()

		


	def stop(self):
		if self.server is not None:
			self.server.stop()
