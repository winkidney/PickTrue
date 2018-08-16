import re

from picktrue.meta import ImageItem
from picktrue.sites.abstract import DummySite, DummyFetcher

from pixivpy3 import (
    AppPixivAPI
)


def normalize_proxy_string(proxy):
    if 'socks5' in proxy:
        if 'socks5h' not in proxy:
            proxy = proxy.replace('socks5', 'socks5h')
    return proxy


def normalize_filename(filename):
    filename = filename.replace("../", "_")
    filename = filename.replace("..\\", "_")
    filename = filename.replace("\\", "_")
    return filename


class PixivFetcher(DummyFetcher):

    def __init__(self, **kwargs):
        super(PixivFetcher, self).__init__(**kwargs)
        self.session.headers.update(
            {'Referer': 'http://www.pixiv.net/'}
        )


class Pixiv(DummySite):

    def __init__(self, url, username, password, proxy=None):
        proxies = {}
        if proxy is not None:
            proxy = normalize_proxy_string(proxy)
            proxies = {
                'proxies': {
                    'http': proxy,
                    'https': proxy,
                }
            }
        requests_kwargs = {
            "timeout": (3, 10),
        }
        requests_kwargs.update(proxies)
        self.api = AppPixivAPI(
            **requests_kwargs
        )
        self._fetcher = PixivFetcher(**proxies)
        self.api.login(username, password)
        self._user_id = int(re.findall('id=(\d+)', url)[0])
        self._dir_name = None
        self._total_illustrations = 0
        self._fetch_user_detail()

    @property
    def fetcher(self):
        return self._fetcher

    @property
    def dir_name(self):
        assert self._dir_name is not None
        return self._dir_name

    def _fetch_user_detail(self):
        assert self._user_id is not None
        profile = self.api.user_detail(self._user_id)
        user = profile['user']
        self._dir_name = "-".join(
            [
                user['name'],
                user['account'],
                str(user['id']),
            ]
        )
        self._dir_name = normalize_filename(self._dir_name)
        self._total_illustrations = profile['profile']['total_illusts']
        return self.dir_name

    def _fetch_image_list(self, ):
        ret = self.api.user_illusts(self._user_id)
        while True:
            for illustration in ret.illusts:
                url = illustration['image_urls']['large']
                file_name = '%s.%s' % (
                    illustration['id'],
                    url.split('.')[-1]
                )
                yield ImageItem(
                    name=file_name,
                    url=url,
                )
            if ret.next_url is None:
                break
            ret = self.api.user_illusts(
                **self.api.parse_qs(ret.next_url)
            )

    def _fetch_single_image_url(self, illustration_id):
        json_result = self.api.illust_detail(illustration_id)
        illustration_info = json_result.illust
        return illustration_info.image_urls['large']

    @property
    def tasks(self):
        yield from self._fetch_image_list()
