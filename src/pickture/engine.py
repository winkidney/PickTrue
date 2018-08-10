from collections import namedtuple
from queue import Queue, Empty
from threading import Thread
import time
from functools import wraps

import requests

from pickture.logger import download_logger


TaskItem = namedtuple(
    'TaskItem',
    (
        'args',
        'kwargs',
    )
)


class StoppableThread(Thread):

    def __init__(
            self, queue, target
    ):
        """
        :type queue: Queue.Queue
        """
        super(StoppableThread, self).__init__()
        self.task_func = target
        self.queue = queue
        self.daemon = True
        self._stopped = False

    def run(self):
        while not self._stopped:
            try:
                task = self.queue.get(timeout=5)
            except Empty:
                continue
            else:
                args = task.args or []
                kwargs = task.args or {}
                self.task_func(*args, **kwargs)

    def stop(self):
        self._stopped = True


def retry(max_retries=3):

    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                retries += 1
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if retries > max_retries:
                        download_logger.exception("Error occurs while execute function\n")
                        break
                    time.sleep(1)
            return None
        return wrapped

    return wrapper


@retry
def download_then_save(url, save_path):
    """
    :return True if download ok
    """
    response = requests.get(url, timeout=(2, 10))
    if response is None:
        download_logger.error("Failed to download image: %s" % url)
        return
    with open(save_path, "wb") as f:
        f.write(response.content)
    return True


class Downloader:

    def __init__(self, num_workers=5, save_dir='.'):
        self.num_workers = num_workers
        self._download_queue = Queue()
        self._download_workers = [
            StoppableThread(
                self._download_queue,
                download_then_save
            )
        ]

    def start(self):
        for worker in self._download_workers:
            worker.start()

    def stop(self):
        for worker in self._download_workers:
            worker.stop()

        for worker in self._download_workers:
            worker.join()
