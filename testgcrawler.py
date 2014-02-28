# -*- coding: utf-8 -*-
"""
    test gcrawler
    ~~~~~~~~~~~~~~~~
    BSD License.
    2011-12 by raptor.zh@gmail.com.
"""
import threading
from gcrawler import Scheduler
import unittest
import urllib2
import logging
import traceback
from datetime import datetime
import re

logging.basicConfig(level=logging.DEBUG)

urls = ['http://www.163.com', 'http://www.qq.com', 'http://www.sina.com.cn',
        'http://www.sohu.com', 'http://www.yahoo.com', 'http://www.baidu.com',
        'http://www.apple.com', 'http://www.microsoft.com']


class Crawler:
    def parser(self, req_url, data):
        return [len(data)]

    def pipeline(self, response):
        url = response.request.url
        print "Data fetched: %s %s" % (url, response.result[0])


class TestGCrawler(unittest.TestCase):
    def testCrawler(self):
        dt = datetime.now()
        crawler = Crawler()
        Scheduler(urls, crawler.parser, crawler.pipeline, 8)
        print datetime.now() - dt


unittest.main()
