import unittest

from gevent import monkey
monkey.patch_all()

import urllib2
import urllib
import random
import multiprocessing
import re
import signal

from gevent.pool import Pool

from ServerTrack.service import ServerTrack

def run_server():
	service = ServerTrack(pool_size = 20)
	service.run()



class ServerTrackTest(unittest.TestCase):

	host = 'http://localhost:8080'

	RE_RESULT_PARSER = re.compile(r'^t=([0-9\-:T]+) cpu=([0-9\.]+) mem=([0-9\.]+) s=([0-9]+) int=([0-9]+)$')

	def setUp(self):
		random.seed(12345)
		self.service = multiprocessing.Process(target = run_server)
		self.service.start()

		def quit(sig, frame):
			self.service.join()

		signal.signal(signal.SIGINT, quit)

	def tearDown(self):
		self.service.join()

	@staticmethod
	def post(request_pair):
		url, data = request_pair # gevent.pool.Pool.map() passes this as a single arg.
		req = urllib2.urlopen(url, data = urllib.urlencode(data))
		return req.getcode()

	@classmethod
	def retr(cls, url):
		req = urllib2.urlopen(cls.host + url)
		return req.getcode(), req.read()

	def parse_result(self, result):
		for match in self.RE_RESULT_PARSER.match(result):
			yield int(match.group(4))

	def testPushHostRecords(self):
		total_records = 1000
		hosts = [ 'alpha', 'bravo' ]
		request_queue = []

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
		print result

		code, result = self.retr('/perf/bravo/last_minute')
		print result
	

