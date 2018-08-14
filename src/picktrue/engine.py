from collections import namedtuple
import os
from queue import Queue, Empty
from threading import Thread
import time
from functools import wraps

import requests

from picktrue.logger import download_logger
from picktrue.utils import run_as_thread


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
        :type queue: queue.Queue
        """
        super(StoppableThread, self).__init__()
        self.task_func = target
        self.queue = queue
        self.daemon = True
        self._stopped = False

    def run(self):
        while not self._stopped:
            try:
                task = self.queue.get(timeout=0.2)
            except Empty:
                continue
            else:
                args = task.args or ()
                kwargs = task.kwargs or {}
                self.task_func(*args, **kwargs)
                self.queue.task_done()

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


@retry()
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


class Counter:

    def __init__(self, total=0):
        self.total = total
        self.done = 0

    def on_change(self):
        print(self.format(), end='\r', flush=True)

    def increment_done(self):
        self.done += 1
        self.on_change()

    def increment_total(self):
        self.total += 1
        self.on_change()

    def format(self):
        return "total: %s, done: %s" % (self.total, self.done)


class Downloader:

    def __init__(self, num_workers=5, save_dir='.'):
        self.save_dir = save_dir
        self.num_workers = num_workers
        self._download_queue = Queue()
        self.counter = Counter()
        self.done = False
        self._stop = False
        self._all_task_add = False
        self.ensure_dir()

        def counter_wrapper(func):

            @wraps(func)
            def wrapped(*args, **kwargs):
                ret = func(*args, **kwargs)
                self.counter.increment_done()
                return ret

            return wrapped

        _dts = counter_wrapper(download_then_save)

        self._download_workers = [
            StoppableThread(
                self._download_queue,
                _dts,
            ) for _ in range(num_workers)
        ]
        self._start_daemons()

    def ensure_dir(self):
        if not os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)

    def add_task(self, task_iter, background=False):
        if background:
            run_as_thread(self._add_task, task_iter)
        else:
            self._add_task(task_iter)

    def _add_task(self, task_iter):
        for task in task_iter:
            if self._stop:
                break
            self.counter.increment_total()
            self._download_queue.put(
                TaskItem(
                    args=(),
                    kwargs={
                        'url': task.url,
                        'save_path': os.path.join(self.save_dir, task.name)
                    },
                )
            )
        self._all_task_add = True

    def _start_daemons(self):
        for worker in self._download_workers:
            worker.start()

    def join(self, background=False):

        def run():
            while not self._all_task_add:
                time.sleep(0.2)
                self._download_queue.join()
            self.done = True

        if background:
            run_as_thread(run)
        else:
            run()

    def stop(self):
        self._stop = True
        for worker in self._download_workers:
            worker.stop()

        for worker in self._download_workers:
            worker.join()
