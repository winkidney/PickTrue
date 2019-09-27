import queue
from queue import Queue


class BrowserRequester:
    def __init__(self):
        self.recv_queue = Queue()
        self.send_queue = Queue()

    def get_request(self, timeout=None):
        if timeout is not None:
            try:
                return self.send_queue.get(
                    timeout=timeout
                )
            except queue.Empty:
                return None
        return self.send_queue.get()

    def send_and_wait(self, url):
        self.send_request(url)
        return self.get_response()

    def send_request(self, url):
        return self.send_queue.put(url)

    def submit_response(self, resp):
        self.recv_queue.put(resp)

    def get_response(self):
        return self.recv_queue.get()
