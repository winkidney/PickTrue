import requests
from pyquery import PyQuery as PQ

from picktrue.meta import ImageItem, UA
from picktrue.sites.abstract import DummySite, DummyFetcher
from picktrue.sites.utils import get_filename_fom_url

ALBUM_URL_TPL = "https://www.douban.com/photos/album/{album_id}/"


def _get_large_img_url(small_img_url):
    return small_img_url.replace("/m/", "/l/")


def _get_album_url(album_id, m_start=None):
    url = ALBUM_URL_TPL.format(album_id=album_id)
    if m_start is not None:
        url = url + "?m_start=%s" % m_start
    return url


def _parse_page(page_html):
    pq = PQ(page_html)
    images = pq(".photolst_photo img")
    images = [PQ(img).attr("src") for img in images]
    images = [_get_large_img_url(img_url) for img_url in images]
    return images


def _get_album_id_form_init_url(url):
    return url.split("/")[-2]


def parse_page(page_html, previous_m_start=None):
    new_m_start = previous_m_start or 0
    images = _parse_page(page_html)
    new_m_start += len(images)
    has_next = len(images) >= 18
    return images, has_next, new_m_start


def get_images(album_home_url, album_id):
    has_next = True
    session = requests.Session()
    session.headers.update(UA)
    album_url = album_home_url
    m_start = None

    while has_next:
        resp = session.get(
            url=album_url,
        )
        if resp.status_code != 200:
            raise ValueError(
                "Failed to fetch douban meta info, code: %s" % resp.status_code
            )
        images, has_next, m_start = parse_page(
            resp.text,
            m_start,
        )
        album_url = _get_album_url(album_id, m_start)
        for image_url in images:
            yield image_url


class DoubanPersonalAlbum(DummySite):

    fetcher = DummyFetcher()

    def __init__(self, album_url):
        self.base_url = album_url
        self.album_id = _get_album_id_form_init_url(album_url)

    @property
    def dir_name(self):
        return self.album_id

    @property
    def tasks(self):
        for image_url in get_images(self.base_url, self.album_id):
            yield ImageItem(
                url=image_url,
                name=get_filename_fom_url(image_url),
            )
