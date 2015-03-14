
from gevent import monkey
monkey.patch_all()

from gevent.pool import Pool
from gevent.wsgi import WSGIServer
from gevent.queue import Queue
from gevent import spawn

import urlparse
import time
import re

from stats import StatsCollector, groupRecordsByTimeBasis

class ServerTrack(object):

	RE_URI_PARSE = re.compile(r'^/perf/([A-Za-z0-9]{2,128})/(last_hour|last_day|last_minute)?')

	def __init__(self, pool_size = 20, max_history_duration = 3600 * 24, service_port = 8080):
		self.pool_size = 20
		self.server = None
		self.service_port = service_port
		self.max_history_duration = int(max_history_duration) # seconds

	def run(self):
		collector = StatsCollector(max_duration = self.max_history_duration)
		pool = Pool(self.pool_size)

		stats_modes = {
			'last_minute': (60, 1), # duration 60 seconds, interval 1 second
			'last_hour': (3600, 60), # duration 60 minutes, interval 1 minute
			'last_day': (24 * 3600, 3600) # duration 24 hours, interval 60 minutes
		}

		def assemble_stats(server_name, now, duration, interval):
			query = collector.query(duration, hostname = server_name)
			for time_id, records in groupRecordsByTimeBasis(query, interval):
				cpuload = sum([ rec.get('cpuload') for rec in records ])
				memload = sum([ rec.get('memload') for rec in records ])
				yield {
					'time': time_id,
					'cpuload': cpuload / len(records),
					'memload': memload / len(records)
				}


		def retrieve_stats(start_response, server_name, stats_mode):
			if stats_mode in stats_modes:
				duration, interval = stats_modes[stats_mode]
			else:
				start_response('400 Bad Request', [])
				return []

		
			now = time.time()
			stats = assemble_stats(server_name, now, duration, interval)
			start_response('200 OK', [])
			return [ 't{time} {cpuload} {memload}'.format(**i) for i in stats ]
	


		def post_stats(start_response, server_name, req_body):
			if req_body is not None:
				params = urlparse.parse_qs(req_body.read())
				sample_time = int(params.get('timestamp', time.time()))
				collector.push(
					timestmap = sample_time,
					hostname = server_name,
					cpuload = float(params.get('cpuload', [])[0]),
					memload = float(params.get('memload', [])[0])
				)

				start_response('201 Created', [])
				return []
			else:
				start_response('400 Bad Request', [])


		def listener(env, start_response):
			method = env.get('REQUEST_METHOD')
			uri = env.get('SCRIPT_NAME', '') + env.get('PATH_INFO', '')
			req = self.RE_URI_PARSE.match(uri)

			if method == 'GET':
				if req is not None:
					return retrieve_stats(start_response, req.group(1), req.group(2))
				else:
					start_response('404 Not Found', [])
					return []
			if method == 'POST':
				if req is not None:
					return post_stats(start_response, req.group(1), env.get('wsgi.input', None))
				else:
					start_response('404 Not Found', [])
					return []



		self.server = WSGIServer(('', self.service_port), listener, spawn = pool)
		self.server.serve_forever()


	def stop(self):
		if self.server is not None:
			self.server.stop()
