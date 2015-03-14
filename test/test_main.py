import unittest

from gevent import monkey
monkey.patch_all()

import urllib2
import urllib
import random
import threading
import signal
import time
import json

from gevent.pool import Pool

from ServerTrack.service import ServerTrack

def run_server():
	service = ServerTrack(pool_size = 20)
	thread = threading.Thread(target = service.run)
	thread.start()
	return thread, service




class ServerTrackTest(unittest.TestCase):

	host = 'http://localhost:8080'

	def setUp(self):
		random.seed(12345)

	def tearDown(self):
		pass
	

	@staticmethod
	def post(request_pair):
		url, data = request_pair # gevent.pool.Pool.map() passes this as a single arg.
		req = urllib2.urlopen(url, data = urllib.urlencode(data))
		return req.getcode()

	@classmethod
	def retr(cls, url):
		req = urllib2.urlopen(cls.host + url)
		return req.getcode(), req.read()

	def parse_result_samples(self, result):
		data = json.loads(result)
		for record in data:
			yield int(record['samples'])

	def testPushHostRecords(self):
		total_records = 1000
		hosts = [ 'alpha', 'bravo' ]
		request_queue = []

		thread, service = run_server() # Starts the service

		for i in range(1, total_records, 1):
			current_url = '{host}/perf/{name}/'.format(
				host = self.host,
				name = hosts[ int((random.random() * 10) % len(hosts)) ]
			)
			request_queue.append((current_url, {
				'cpuload': random.random() * 10,
				'memload': random.random() * 10
			}))

		pool = Pool(20)
		pool.map(self.post, request_queue)


		code, result = self.retr('/perf/alpha/last_minute')
		samples_alpha = self.parse_result_samples(result)


		code, result = self.retr('/perf/bravo/last_minute')
		samples_bravo = self.parse_result_samples(result)

		service.stop()
		thread.join()

		total_samples = sum(list(samples_alpha) + list(samples_bravo))
		self.assertEqual(total_samples, total_records)
	

