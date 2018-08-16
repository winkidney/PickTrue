from abc import abstractmethod
import os

import requests
from picktrue.utils import retry


class DummySite:

    def dir_name(self):
        raise NotImplementedError

    @property
    def fetcher(self):
        raise NotImplementedError()

    @property
    def tasks(self):
        raise NotImplementedError()


class DummyFetcher:

    def __init__(self, proxies=None):
        self.session = requests.session()
        if proxies is not None:
            self.session.proxies = proxies

    @retry()
    def get(self, url, **kwargs):
        """
        :rtype: requests.Response
        """
        if 'timeout' in kwargs:
            kwargs.pop('timeout')
        return self.session.get(url, timeout=(2, 30), **kwargs)

    def save(self, content, task_item):
        """
        :type content: bytearray
        :type task_item: picktrue.meta.TaskItem
        """
        image = task_item.image
        save_path = os.path.join(
            task_item.base_save_path,
            image.name,
        )
        with open(save_path, "wb") as f:
            f.write(content)
