import os
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


def guess_extension(image_url):
    return image_url.split('.')[-1]


def normalize_filename(filename):
    filename = filename.replace("../", "_")
    filename = filename.replace("..\\", "_")
    filename = filename.replace("\\", "_")
    return filename


def parse_image_urls(illustration):
    if 'original_image_url' in illustration['meta_single_page']:
        url = illustration['meta_single_page']['original_image_url']
        if illustration['type'] == 'ugoira':
            url = url.replace("img-original", 'img-zip-ugoira')
            url = re.findall('(.*)_ugoira0\..*', url)[0]
            url = "%s%s" % (url, '_ugoira1920x1080.zip')
        file_name = '%s.%s' % (
            illustration['id'],
            guess_extension(url)
        )
        yield ImageItem(
            name=file_name,
            url=url,
        )
    else:
        dir_name = normalize_filename(illustration['title'])
        images = illustration['meta_pages']
        for index, image in enumerate(images):
            url = image['image_urls']['original']
            name = "%s.%s" % (index, guess_extension(url))
            yield ImageItem(
                name=name,
                url=url,
                meta={
                    'is_comic': True,
                    'dir_name': dir_name,
                }
            )


class PixivFetcher(DummyFetcher):

    def __init__(self, **kwargs):
        super(PixivFetcher, self).__init__(**kwargs)
        self.session.headers.update(
            {'Referer': 'http://www.pixiv.net/'}
        )

    def save(self, content, task_item):
        if task_item.image.meta is None:
            return super(PixivFetcher, self).save(content, task_item)
        image = task_item.image
        save_path = os.path.join(
            task_item.base_save_path,
            image.meta['dir_name'],
        )
        os.makedirs(save_path, exist_ok=True)
        save_path = self._safe_path(save_path)
        save_path = os.path.join(
            save_path,
            image.name,
        )
        with open(save_path, "wb") as f:
            f.write(content)


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
                yield from parse_image_urls(illustration)
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
