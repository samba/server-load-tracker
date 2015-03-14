import unittest

from gevent import monkey
monkey.patch_all()

import urllib2
import urllib
import random
import multiprocessing
import re


from ServerTrack.daemon import ServerTrack

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

	def tearDown(self):
		self.service.join()

	def post(self, url, data):
		req = urllib2.urlopen(self.host + url, data = urllib.urlencode(data))
		return req.getcode()

	def retr(self, url):
		req = urllib2.urlopen(self.host + url)
		return req.getcode(), req.read()

	def parse_result(self, result):
		for match in self.RE_RESULT_PARSER.match(result):
			yield int(match.group(4))

	def testPushHostRecords(self):
		total_records = 1000
		hosts = [ 'alpha', 'bravo' ]

		def printResult(query):
			code, result = self.retr(query)
			self.assertEqual(code, 200)
			print result

		for i in range(1, total_records, 1):
			current_host = hosts[ int((random.random() * 10) % len(hosts)) ]
			code = self.post('/perf/{host}/'.format(host = current_host), {
				'cpuload': random.random() * 10,
				'memload': random.random() * 10
			})

		printResult('/perf/alpha/last_minute')
		printResult('/perf/bravo/last_minute')
	

