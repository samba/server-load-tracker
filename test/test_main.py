import unittest

from gevent import monkey
monkey.patch_all()

import urllib2
import urllib
import random
import multiprocessing


from ServerTrack.daemon import ServerTrack

def run_server():
	service = ServerTrack(pool_size = 20)
	service.run()


class ServerTrackTest(unittest.TestCase):

	host = 'http://localhost:8080'

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

	def testPushHostAlpha(self):
		for i in range(1, 3000, 1):
			print 'Request #{0:d}'.format(i)
			code = self.post('/perf/alpha/', {
				'cpuload': random.random(),
				'memload': random.random()
			})

		code, result = self.retr('/perf/alpha/last_hour')
		self.assertEqual(code, 200)
		print result
