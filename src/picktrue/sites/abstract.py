import requests
from picktrue.utils import retry


class DummySite:

    @property
    def fetcher(self):
        raise NotImplementedError()

    @property
    def tasks(self):
        raise NotImplementedError()


class DummyFetcher:

    def __init__(self):
        self.session = requests.session()

    @retry()
    def get(self, url, **kwargs):
        """
        :rtype: requests.Response
        """
        if 'timeout' in kwargs:
            kwargs.pop('timeout')
        return self.session.get(url, timeout=(2, 30), **kwargs)
