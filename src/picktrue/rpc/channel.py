import json
import queue
import time
from queue import Queue
from threading import Lock

from picktrue.utils import run_as_thread


class BrowserRequester:
    def __init__(self):
        self.recv_queue = Queue()
        self.send_queue = Queue()
        self._t = run_as_thread(self.start_recv)
        self._lock_registry = {}
        self._ret_registry = {}

    def start_recv(self):
        while True:
            raw = self.recv_queue.get()
            ret_meta = json.loads(raw)
            url = ret_meta['request_url']
            data = ret_meta['response']
            self._ret_registry[url] = data
            self._lock_registry[url].release()

    def get_request(self, timeout=None):
        if timeout is not None:
            try:
                return self.send_queue.get(
                    timeout=timeout
                )
            except queue.Empty:
                return None
        return self.send_queue.get()

    def send_and_wait(self, url, timeout=None, max_retry=0):
        retried = 0
        while True:
            self.send_request(url)
            ret = self.get_response(url, timeout=timeout)
            if ret is None:
                retried += 1
                time.sleep(5)
            else:
                return ret
            if retried > max_retry:
                raise ValueError("Failed to get url: %s" % url)

    def send_request(self, url):
        self._lock_registry[url] = Lock()
        self._lock_registry[url].acquire()
        self.send_queue.put(url)

    def submit_response(self, resp):
        self.recv_queue.put(resp)

    def get_response(self, url, timeout=None):
        got = self._lock_registry[url].acquire(timeout=timeout)
        if got:
            ret = self._ret_registry[url]
            del self._ret_registry[url]
            del self._lock_registry[url]
            return ret
        else:
            return None
