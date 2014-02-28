# -*- coding: utf-8 -*-
"""
    gevent crawler
    ~~~~~~~~~~~~~~~~
    BSD License
    2011-12 by raptor.zh@gmail.com.
"""
import threading
import gevent
from gevent import monkey, queue

gevent.monkey.patch_all()

import urllib2
import logging

logger = logging.getLogger(__name__)


def retryOnURLError(trycnt=3):
    def funcwrapper(fn):
        def wrapper(self, *args, **kwargs):
            for i in range(trycnt):
                try:
                    return fn(self, *args, **kwargs)
                except urllib2.URLError, e:
                    logger.info("retry %s time(s)" % (i + 1))
                    if i == trycnt - 1:
                        raise e
        return wrapper
    return funcwrapper


class Request:
    def __init__(self, url="", parser=None):
        self.url    = url
        self.parser = parser


class Response:
    def __init__(self, request=None, result=None):
        self.request = request
        self.result  = result


class Scheduler:
    def __init__(self, urls, parser, pipeline, max_running=20):
        self.pipeline = pipeline
        self.pendings = queue.Queue(-1)
        self.responses = queue.Queue(-1)
        self.max_running = max_running
        for url in urls:
            self.pendings.put(Request(url=url, parser=parser))
        gevent.spawn(self.doSchedule).join()

    @retryOnURLError()
    def fetch(self, url):
        f = urllib2.urlopen(url)
        data = f.read()
        f.close()
        return data

    def parser(self, req):
        results = []
        try:
            data = self.fetch(req.url)
            if req.parser != None:
                res = req.parser(req.url, data)
                for r in res:
                    if type(r) == type(Request()) and r.__class__ == Request:
                        self.pendings.put(r)
                    else:
                        results.append(r)
            else:
                results.append(data)
        except:
            import traceback
            traceback.print_exc()
            results = None
        self.responses.put(Response(request=req, result=results))

    def doSchedule(self):
        runnings = 0
        while runnings > 0 or not self.pendings.empty():
            try:
                while runnings < self.max_running:
                    req = self.pendings.get_nowait()
                    logger.debug("new greenlet for: %s" % req.url)
                    gevent.spawn(self.parser, req)
                    runnings += 1
            except queue.Empty:
                pass
            resp = self.responses.get()
            runnings -= 1
            if resp.result == None:  # None means error!
                logger.error("Fetch fail: %s" % resp.request.url)
            elif resp.result != []:
                try:
                    self.pipeline(resp)
                except:
                    import traceback
                    traceback.print_exc()
