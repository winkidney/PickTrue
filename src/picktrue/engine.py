from typing import NamedTuple

import os
from queue import Queue, Empty
from threading import Thread
import time
from functools import wraps

from picktrue.logger import download_logger
from picktrue.meta import DownloadTaskItem
from picktrue.utils import run_as_thread


class WorkerTask(NamedTuple):
    kwargs: dict = None
    args: tuple = None


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


def mk_download_save_function(fetcher):
    """
    :type fetcher: picktrue.sites.abstract.DummyFetcher
    """

    def download_then_save(task_item):
        """
        :return True if download ok
        :type task_item: picktrue.meta.TaskItem
        """
        response = fetcher.get(task_item.image.url)
        if response is None:
            download_logger.error("Failed to download image: %s" % task_item.image.url)
            return
        fetcher.save(response.content, task_item)
        return True

    return download_then_save


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

    def __init__(self, fetcher, num_workers=5, save_dir='.'):
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
            def wrapped(task_item):
                ret = func(task_item=task_item)
                self.counter.increment_done()
                return ret

            return wrapped

        download_then_save = mk_download_save_function(
            fetcher
        )

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

    def _add_task(self, image_iter):
        for image in image_iter:
            if self._stop:
                break
            dti = DownloadTaskItem(
                image=image,
                base_save_path=self.save_dir,
            )
            self.counter.increment_total()
            self._download_queue.put(
                WorkerTask(
                    kwargs={
                        'task_item': dti,
                    }
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

    def describe(self):
        return "%s of %s downloaded" % (
            self.counter.done,
            self.counter.total,
        )
