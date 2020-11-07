import os
from pathlib import Path

import requests

from picktrue.meta import UA, ImageItem
from picktrue.utils import retry


def normalize_proxy_string(proxy):
    if 'socks5' in proxy:
        if 'socks5h' not in proxy:
            proxy = proxy.replace('socks5', 'socks5h')
    return proxy


def get_proxy(proxy_string=None):
    if proxy_string is None:
        return {}
    proxy = normalize_proxy_string(proxy_string)
    proxies = {
        'proxies': {
            'http': proxy,
            'https': proxy,
        }
    }
    return proxies


class DummySite:

    @property
    def dir_name(self):
        raise NotImplementedError()

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
        self.session.headers.update(UA)

    @staticmethod
    def _safe_name(name):
        name = name.replace("/", " ")
        name = name.replace("\\", " ")
        name = name.strip()
        name = name.replace(" ", '-')
        return name

    @staticmethod
    def _safe_path(path):
        return Path(path).absolute()

    @retry()
    def get(self, url, **kwargs):
        """
        :rtype: requests.Response
        """
        if 'timeout' in kwargs:
            kwargs.pop('timeout')
        return self.session.get(url, timeout=(2, 30), **kwargs)

    def get_save_path(self, base_path, image_name, image: ImageItem):
        save_path = os.path.join(
            base_path,
            image_name,
        )
        return save_path

    def save(self, content, task_item):
        """
        :type content: bytearray
        :type task_item: picktrue.meta.TaskItem
        """
        image = task_item.image
        image_name = image.name
        if callable(image.name):
            image_name = image.name(image.url, content)
        save_path = self.get_save_path(
            base_path=task_item.base_save_path,
            image_name=image_name,
            image=image,
        )
        save_path = self._safe_path(save_path)
        if os.path.exists(save_path):
            return
        with open(save_path, "wb") as f:
            f.write(content)
