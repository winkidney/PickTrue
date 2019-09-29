import hashlib
import time
from urllib.parse import urljoin

import requests

from picktrue.meta import ImageItem, UA
from picktrue.rpc.taskserver import server
from picktrue.sites.abstract import DummySite, DummyFetcher, get_proxy


BASE_URL = "https://www.artstation.com/"
PROJECT_URL_TPL = '/users/{user_id}/projects.json?page={page}'
DETAIL_URL_TPL = '/projects/{hash_id}.json'


def _get_file_hash(file_content):
    m = hashlib.md5()
    m.update(file_content)
    return m.digest().hex()


def get_name_from_url(img_url: str, file_content):
    file_name = img_url.split(
        '/'
    )[-1]
    file_name = file_name.split('?')[:-1]
    file_name = '?'.join(file_name)
    name_postfix = _get_file_hash(file_content)
    name = file_name.split('.')[:-1]
    name = ".".join(name)
    ext = file_name.split('.')[-1]
    file_name = "-".join([name, name_postfix])
    file_name = ".".join([file_name, ext])
    return file_name


def parse_single_artwork(artwork_dict: dict):
    """
    {
        "liked":false,
        "tags":[

        ],
        "hide_as_adult":false,
        "visible_on_artstation":true,
        "assets":[
            {
                "has_image":true,
                "has_embedded_player":false,
                "player_embedded":null,
                "oembed":null,
                "id":12260469,
                "title_formatted":"",
                "image_url":"https://cdnb.artstation.com/p/assets/images/images/012/260/469/large/ham-sung-choul-braveking-180809-1-mini.jpg?1533864344",
                "width":1300,
                "height":2434,
                "position":0,
                "asset_type":"image",
                "viewport_constraint_type":"constrained"
            },
            {
                "has_image":false,
                "has_embedded_player":false,
                "player_embedded":null,
                "oembed":null,
                "id":12260473,
                "title_formatted":"",
                "image_url":"https://cdnb.artstation.com/p/assets/covers/images/012/260/473/large/ham-sung-choul-braveking-180809-1-mini-2.jpg?1533864353",
                "width":822,
                "height":822,
                "position":1,
                "asset_type":"cover",
                "viewport_constraint_type":"constrained"
            }
        ],
        "collections":[

        ],
        "user":{
            "followed":true,
            "following_back":false,
            "blocked":false,
            "is_staff":false,
            "id":199106,
            "username":"braveking",
            "headline":"freelance artist",
            "full_name":"Ham Sung-Choul(braveking)",
            "permalink":"https://www.artstation.com/braveking",
            "medium_avatar_url":"https://cdna.artstation.com/p/users/avatars/000/199/106/medium/ab27ac7f48de117074c14963a3371914.jpg?1461412259",
            "large_avatar_url":"https://cdna.artstation.com/p/users/avatars/000/199/106/large/ab27ac7f48de117074c14963a3371914.jpg?1461412259",
            "small_cover_url":"https://cdn.artstation.com/static_media/placeholders/user/cover/default.jpg",
            "pro_member":false
        },
        "medium":null,
        "categories":[
            {
                "name":"Characters",
                "id":1
            },
            {
                "name":"Fantasy",
                "id":2
            },
            {
                "name":"Concept Art",
                "id":3
            }
        ],
        "software_items":[

        ],
        "id":3513664,
        "user_id":199106,
        "title":"doodle",
        "description":"<p></p>",
        "description_html":"<p></p>",
        "created_at":"2018-08-09T07:50:11.347-05:00",
        "updated_at":"2018-08-10T01:55:50.964-05:00",
        "views_count":3257,
        "likes_count":699,
        "comments_count":1,
        "permalink":"https://www.artstation.com/artwork/mr5aZ",
        "cover_url":"https://cdnb.artstation.com/p/assets/covers/images/012/260/473/medium/ham-sung-choul-braveking-180809-1-mini-2.jpg?1533864353",
        "published_at":"2018-08-09T07:50:19.308-05:00",
        "editor_pick":true,
        "adult_content":false,
        "admin_adult_content":false,
        "slug":"doodle-184-a5ea10f5-e98e-46e2-866e-63ae54fd443a",
        "suppressed":false,
        "hash_id":"mr5aZ",
        "visible":true
    }
    :rtype: list[ImageItem]
    """
    assets = artwork_dict['assets']
    assets = [
        asset for asset in assets
        if asset['has_image']
    ]
    images = (
        ImageItem(
            url=asset['image_url'],
            name=get_name_from_url,
        )
        for asset in assets
    )
    return images


def parse_artwork_url(item_dict):
    """
    {
    "data":
        [
            {
                "id":3497866,
                "user_id":199106,
                "title":"doodle",
                "description":"",
                "created_at":"2018-08-06T04:23:20.695-05:00",
                "updated_at":"2018-08-10T01:39:27.162-05:00",
                "likes_count":340,
                "slug":"doodle-184-669828ca-6a1b-4fc7-986d-e4eeaa4b5d55",
                "published_at":"2018-08-06T04:24:58.518-05:00",
                "adult_content":false,
                "cover_asset_id":12192935,
                "admin_adult_content":false,
                "hash_id":"KnrbX",
                "permalink":"https://www.artstation.com/artwork/KnrbX",
                "hide_as_adult":false,
                "cover":{
                    "id":12192935,
                    "small_image_url":"https://cdnb.artstation.com/p/assets/covers/images/012/192/935/small/ham-sung-choul-braveking-180806-1-b-mini-3.jpg?1533547474",
                    "medium_image_url":"https://cdnb.artstation.com/p/assets/covers/images/012/192/935/medium/ham-sung-choul-braveking-180806-1-b-mini-3.jpg?1533547474",
                    "small_square_url":"https://cdnb.artstation.com/p/assets/covers/images/012/192/935/small_square/ham-sung-choul-braveking-180806-1-b-mini-3.jpg?1533547474",
                    "thumb_url":"https://cdnb.artstation.com/p/assets/covers/images/012/192/935/smaller_square/ham-sung-choul-braveking-180806-1-b-mini-3.jpg?1533547474",
                    "micro_square_image_url":"https://cdnb.artstation.com/p/assets/covers/images/012/192/935/micro_square/ham-sung-choul-braveking-180806-1-b-mini-3.jpg?1533547474",
                    "aspect":1
                },
                "icons":{
                    "image":false,
                    "video":false,
                    "model3d":false,
                    "marmoset":false,
                    "pano":false
                },
                "assets_count":1
            },
        ],
        "total_count":38
    }
    """
    url = urljoin(
        BASE_URL,
        DETAIL_URL_TPL.format(
            hash_id=item_dict['hash_id']
        )
    )
    return url


def get_project_page_url(user_id, page=1):
    path = PROJECT_URL_TPL.format(
        user_id=user_id,
        page=page,
    )
    url = urljoin(BASE_URL, path)
    return url


def has_next_page(current_count, total_count):
    return current_count < total_count


class BaseMetaFetcher:
    def request_url(self, url):
        raise NotImplementedError

    def get_artwork_summery(self, summary_url):
        return self.request_url(summary_url)

    def get_single_page(self, user_id, page):
        initial_url = get_project_page_url(
            user_id=user_id,
            page=page,
        )
        resp = self.request_url(initial_url)
        print(resp.keys())
        assert 'total_count' in resp
        total_count = resp['total_count']
        data_count = len(resp['data'])
        return total_count, data_count, resp['data']


class LocalMetaFetcher(BaseMetaFetcher):
    def __init__(self, proxies):
        self._proxies = proxies

    def request_url(self, url):
        resp = requests.get(url, headers=UA, proxies=self._proxies)
        return resp.json()


class BrowserMetaFetcher(BaseMetaFetcher):
    server = server

    def __init__(self):
        self.server.start()

    def request_url(self, url):
        return self.server.requester.send_and_wait(url)


class TaskMaker:
    def __init__(self, user_id, meta_fetcher: BaseMetaFetcher):
        self.user_id = user_id
        self.meta = meta_fetcher

    def __call__(self, *args, **kwargs):
        yield from self._gen_tasks()

    def _get_image_item_from_detail(self, artwork_summary):
        summary_url = parse_artwork_url(artwork_summary)
        resp = self.meta.get_artwork_summery(summary_url)
        return parse_single_artwork(resp)

    def _yield_image_items(self, data):
        for summary in data:
            for image_item in self._get_image_item_from_detail(
                summary,
            ):
                yield image_item

    def _gen_tasks(self):
        page = 1
        total_count, current_count, data = self.meta.get_single_page(
            self.user_id,
            page,
        )
        yield from self._yield_image_items(data)
        while has_next_page(current_count, total_count):
            page += 1
            _, count_delta, data = self.meta.get_single_page(
                self.user_id,
                page=page,
            )
            current_count += count_delta
            yield from self._yield_image_items(data)
            time.sleep(0.2)


class ArtStation(DummySite):
    """
    >>> art = ArtStation("https://www.artstation.com/braveking")
    >>> len(list(art.tasks)) > 0
    True
    """

    def __init__(self, user_url: str, proxy=None):
        self._tasks = None
        self.url = user_url
        assert user_url.startswith(BASE_URL)
        self.user_id = user_url.replace(BASE_URL, '')
        self._proxies = get_proxy(proxy)
        self._fetcher = DummyFetcher(**self._proxies)
        self._task_maker = TaskMaker(
            user_id=self.user_id,
            meta_fetcher=BrowserMetaFetcher(),
        )

    @property
    def fetcher(self):
        return self._fetcher

    @property
    def dir_name(self):
        return self.user_id

    @property
    def tasks(self):
        yield from self._task_maker()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
