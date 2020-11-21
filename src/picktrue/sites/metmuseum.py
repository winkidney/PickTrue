import os
import re
from urllib.parse import urlparse, parse_qs

from pyquery import PyQuery

from picktrue.engine import Downloader
from picktrue.meta import ImageItem
from picktrue.rpc.taskserver import BrowserMetaFetcher
from picktrue.sites.abstract import DummySite, DummyFetcher
from picktrue.logger import pk_logger
from picktrue.sites.utils import safe_file_name, get_filename_fom_url

IMAGE_URL_TPL = "http://img.hb.aicdn.com/{file_key}"
BASE_URL = "http://huaban.com"

XHR_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; WOW64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/56.0.2924.87 Safari/537.36",
}


def _get_params(query_parts):
    """
    :param query_parts: just like "material=Archery"
        or "material=Archery&offset=0&perPage=20&sortBy=Relevance&sortOrder=asc&searchField=All&pageSize=0"
    """
    path = urlparse('http://test.com/?' + query_parts)
    return parse_qs(path.query)


class SearchPage:
    def __init__(self, page_url, meta_fetcher: BrowserMetaFetcher):
        """
        html page link:
        https://www.metmuseum.org/art/collection/search#!/search?material=Archery
        https://www.metmuseum.org/art/collection/search#!?material=Archery&offset=0&perPage=20&sortBy=Relevance&sortOrder=asc&searchField=All&pageSize=0
        https://www.metmuseum.org/art/collection/search#!?material=Archery&offset=20&perPage=20&sortBy=Relevance&sortOrder=asc&searchField=All&pageSize=0
        json link:
        https://www.metmuseum.org/mothra/collectionlisting/search?material=Archery&offset=0&pageSize=0&perPage=20&searchField=All&showOnly=&sortBy=Relevance
        """
        query_parts = "?".join(page_url.split("?")[-1:])
        self._params = _get_params(query_parts)
        if "material" not in self._params:
            raise ValueError("Failed to parse url: %s" % page_url)
        self._fetcher = meta_fetcher

    @property
    def dir_name(self):
        return self.safe_search_keyword

    @property
    def safe_search_keyword(self):
        return safe_file_name(self._params["material"][0])

    def get_search_request(self, offset, page_size, per_page):
        tpl = (
            "https://www.metmuseum.org/mothra/collectionlisting/search"
            "?material={keyword}"
            "&offset={offset}"
            "&pageSize={page_size}"
            "&perPage={per_page}"
            "&searchField=All"
            "&showOnly="
            "&sortBy=Relevance"
        )
        return tpl.format(
            keyword=self.safe_search_keyword,
            offset=offset,
            page_size=page_size,
            per_page=per_page,
        )

    def get_image_items(self, ):
        """
        {
          "results": [
            {
              "title": "Archer&#39;s Ring",
              "description": " ",
              "artist": "",
              "culture": "Turkish",
              "teaserText": "<p>Date: 16th–17th century<br/>Accession Number: 36.25.2814</p>",
              "url": "https://www.metmuseum.org/art/collection/search/30142?searchField=All&amp;sortBy=Relevance&amp;what=Archery&amp;ft=*&amp;offset=0&amp;rpp=20&amp;pos=1",
              "image": "https://images.metmuseum.org/CRDImages/aa/mobile-large/LC-36_25_2814-001.jpg",
              "regularImage": "aa/web-additional/LC-36_25_2814-001.jpg",
              "largeImage": "aa/web-large/LC-36_25_2814-001.jpg",
              "date": "16th–17th century",
              "medium": "Bronze",
              "accessionNumber": "36.25.2814",
              "galleryInformation": "Not on view"
            },
        }
        """
        offset = int(self._params.get('offset', [0])[0])
        page_size = int(self._params.get('pageSize', [0])[0])
        per_page = int(self._params.get('perPage', [20])[0])
        while True:
            r = self._fetcher.request_url(
                url=self.get_search_request(
                    offset=offset,
                    page_size=page_size,
                    per_page=per_page,
                ),
            )
            for image_meta in r['results']:
                page_url = image_meta['url']
                items = ItemPage(
                    page_url=page_url,
                    meta_fetcher=self._fetcher,
                    search_keyword=self.safe_search_keyword,
                ).get_image_items()
                if items:
                    for item in items:
                        yield item
            req = r['request']
            offset = req['offset'] + per_page
            print(offset, r['totalResults'])
            if offset > r['totalResults']:
                break


class ItemPage:
    def __init__(self, page_url, meta_fetcher: BrowserMetaFetcher, search_keyword=None):
        """
        https://www.metmuseum.org/art/collection/search/35684?
        searchField=All&sortBy=Relevance&what=Archery&ft=*&offset=0&rpp=20&pos=13
        image:
        https://collectionapi.metmuseum.org/api/collection/v1/iiif/23603/1642473/main-image
        """
        path = urlparse(page_url)
        self._item_id = path.path.split("/")[-1]
        self._fetcher = meta_fetcher
        self._page_url = page_url
        self._search_keyword = search_keyword

    @property
    def dir_name(self):
        if self._search_keyword is not None:
            return safe_file_name(
                self._search_keyword
            )
        else:
            return ""

    def _mk_item(self, image_url, title, has_many=False):
        name = get_filename_fom_url(image_url)
        meta = dict(title=title, has_many=has_many)
        meta['search_keyword'] = self._search_keyword
        return ImageItem(
            image_url,
            name=name,
            meta=meta,
        )

    def get_image_items(self):
        resp = self._fetcher.request_url(
            self._page_url,
        )
        query = PyQuery(resp)
        title = query("#artwork__title").text()
        extra_images = query("img.gtm__carousel__thumbnail")
        main_image = query(".artwork__interaction--download a")
        if len(extra_images) > 0:
            return [
                self._mk_item(
                    PyQuery(img).attr("data-superjumboimage"),
                    title=title,
                    has_many=True,
                )
                for img in extra_images
            ]
        else:
            image_url = main_image.attr("href")
            if not image_url:
                pk_logger.warning("No image available for: %s" % title)
                return []
            return [
                self._mk_item(
                    image_url=image_url,
                    title=title,
                    has_many=False,
                )
            ]


class Fetcher(DummyFetcher):

    def get_save_path(self, base_path, image_name, image: ImageItem):
        project_dir = base_path
        if image.meta['search_keyword']:
            project_dir = os.path.join(image.meta['search_keyword'])
        if image.meta['has_many']:
            project_dir = os.path.join(
                project_dir,
                image.meta['title'],
            )
        else:
            splited = image_name.split(".")
            name, ext = ".".join(splited[:-1]), splited[-1]
            image_name = safe_file_name(image.meta['title'] + name + "." + ext)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir, exist_ok=True)
        return os.path.join(project_dir, image_name)


class MetMuseum(DummySite):

    fetcher = Fetcher()

    def __init__(self, url):
        self._base_url = url
        if "search/" not in url:
            self._iter = SearchPage(
                page_url=self._base_url,
                meta_fetcher=BrowserMetaFetcher(),
            )
        else:
            self._iter = ItemPage(
                page_url=self._base_url,
                meta_fetcher=BrowserMetaFetcher(),
            )

    @property
    def dir_name(self):
        return self._iter.dir_name

    @property
    def tasks(self):
        print(self._iter)
        for item in self._iter.get_image_items():
            yield item


def main():
    import sys
    import time
    site = MetMuseum(
        sys.argv[1],
        # "https://www.metmuseum.org/art/collection/search#!?material=Archery&offset=0&perPage=20&sortBy=Relevance&sortOrder=asc&searchField=All&pageSize=0"
        # "https://www.metmuseum.org/art/collection/search/35684?searchField=All&sortBy=Relevance&what=Archery&ft=*&offset=0&rpp=20&pos=13"
    )
    downloader = Downloader(save_dir=".", fetcher=site.fetcher)
    downloader.add_task(
        site.tasks,
        background=True,
    )
    downloader.join(background=True)
    while not downloader.done:
        time.sleep(5)
        print(downloader.describe())
    print(downloader.describe())


if __name__ == '__main__':
    main()
