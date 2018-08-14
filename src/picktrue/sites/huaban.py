import json
import os
import random
import string
from collections import namedtuple
from urllib.parse import urljoin

from picktrue.meta import ImageItem
from picktrue.sites.abstract import DummySite, DummyFetcher
from picktrue.utils import retry

IMAGE_URL_TPL = "http://img.hb.aicdn.com/{file_key}"
XHR_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; WOW64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/56.0.2924.87 Safari/537.36",
}


Pin = namedtuple(
    'Pin',
    (
        'url',
        'filename',
        'file_to_save',
    )
)


class HuaBanFetcher(DummyFetcher):
    def __init__(self):
        super(HuaBanFetcher, self).__init__()
        self.session.headers.update(
            XHR_HEADERS,
        )

    @retry()
    def get(self, url, require_json=False, **kwargs):
        """
        :param require_json: If require_json is True and
        the result is not json-encoded, will raise error
        then have a retry.
        :rtype: requests.Response
        """
        if 'timeout' in kwargs:
            kwargs.pop('timeout')
        resp = self.session.get(url, timeout=(2, 30), **kwargs)
        if require_json:
            resp.json()
        return resp


def _random_string(length):
    return ''.join(
        random.choice(string.ascii_lowercase + string.digits)
        for _ in range(length)
    )


def _safe_file_name(file_name):
    return file_name.replace("/", "_")


def _get_file_ext(mime_type):
    return mime_type.split("/")[-1]


def get_pins(board_dict):
    board = board_dict
    pins = []
    for info in board['pins']:
        ext = _get_file_ext(info['file']['type'])
        file_name = "%s.%s" % (info['pin_id'], ext)
        meta = {
            "pin_id": info['pin_id'],
            "url": IMAGE_URL_TPL.format(file_key=info['file']['key']),
            'type': info['file']['type'],
            'ext': ext,
            "title": info['raw_text'],
            "link": info['link'],
            "source": info['source'],
            "file_name": file_name
        }
        pins.append(meta)
    return pins


def get_boards(user_meta):
    boards = []
    for board in user_meta['boards']:
        meta = {
            "board_id": board['board_id'],
            "title": board['title'],
            "pins": None,
            "pin_count": board['pin_count'],
            "dir_name": _safe_file_name(board['title']),
        }
        boards.append(meta)
    return boards


class User(object):
    def __init__(self, user_url):
        self.fetcher = HuaBanFetcher()
        self.base_url = user_url
        self.further_url_tpl = urljoin(
            self.base_url,
            "?{random_str}"
            "&max={board_id}"
            "&limit=10"
            "&wfl=1"
        )

        self.username = None
        self.board_count = None
        self.pin_count = None
        self._boards = []

    def _fetch_home(self):
        resp = self.fetcher.get(self.base_url, require_json=True)
        user_meta = resp.json()['user']
        self.username = user_meta['username']
        self.board_count = user_meta['board_count']
        self.pin_count = user_meta['pin_count']
        return get_boards(user_meta)

    def _fetch_further(self, prev_boards):
        max_id = prev_boards[-1]['board_id']
        further_url = self.further_url_tpl.format(
            random_str=_random_string(8),
            board_id=max_id,
        )
        resp = self.fetcher.get(
            further_url,
            require_json=True,
        )
        content = resp.json()
        return get_boards(content['user'])

    def _fetch_boards(self):
        self._boards.extend(self._fetch_home())
        while self.board_count > len(self._boards):
            further_boards = self._fetch_further(self.boards)
            self._boards.extend(further_boards)
        return self._boards

    @property
    def boards(self):
        if not self._boards:
            self._fetch_boards()
        return self._boards

    def as_dict(self):
        return {
            "username": self.username,
            "board_count": self.board_count,
            "boards": self.boards,
        }


class Board(object):
    def __init__(self, board_url_or_id):
        board_url_or_id = str(board_url_or_id)
        self.fetcher = HuaBanFetcher()
        if "http" in board_url_or_id:
            self.base_url = board_url_or_id
        else:
            self.base_url = "http://huaban.com/boards/{board_id}/".format(
                board_id=board_url_or_id
            )
        self.further_pin_url_tpl = urljoin(
            self.base_url,
            "?{random_string}"
            "&max={pin_id}"
            "&limit=20"
            "&wfl=1"
        )

        # uninitialized properties
        self.pin_count = None
        self.title = None
        self.description = None
        self._pins = []

    def _fetch_home(self):
        resp = self.fetcher.get(
            self.base_url,
            require_json=True,
        )
        resp = resp.json()
        board = resp['board']
        self.pin_count = board['pin_count']
        self.title = board['title']
        self.description = board['description']
        return get_pins(board)

    def _fetch_further(self, prev_pins):
        max_id = prev_pins[-1]['pin_id']
        further_url = self.further_pin_url_tpl.format(
            pin_id=max_id,
            random_string=_random_string(8),
        )

        resp = self.fetcher.get(
            further_url,
            require_json=True,
        )
        content = resp.json()
        return get_pins(content['board'])

    def fetch_pins(self):
        self._pins.extend(self._fetch_home())
        yield self._pins
        while self.pin_count > len(self._pins):
            further_pins = self._fetch_further(self._pins)
            if len(further_pins) <= 0:
                break
            self._pins.extend(further_pins)
            yield further_pins

    @property
    def pins(self):
        for pin_group in self.fetch_pins():
            for pin in pin_group:
                yield pin

    def as_dict(self):
        return {
            "pins": self._pins,
            "title": self.title,
            "description": self.description,
            "pin_count": self.pin_count,
        }


def mk_pin(pin_meta, dir_to_save):
    url = pin_meta["url"]
    filename = u"{title}.{ext}".format(
        title=pin_meta['pin_id'],
        ext=pin_meta['ext'],
    )
    file_to_save = os.path.join(
        dir_to_save,
        filename,
    )
    return Pin(
        url=url,
        filename=filename,
        file_to_save=file_to_save
    )


class HuaBan(DummySite):

    fetcher = HuaBanFetcher()

    def __init__(self, user_url):
        self.meta = None
        self.base_url = user_url
        self.user = User(user_url)
        self._boards = []
        self.parsed_pin_count = 0
        self.fetch_initial_meta()

    def fetch_initial_meta(self):
        boards = self.user.boards
        for meta in boards:
            self._boards.append(Board(meta['board_id']))

    @property
    def tasks(self):
        for board, pin in self.boards_pins:
            yield ImageItem(
                url=pin.url
            )

    @property
    def boards_pins(self):
        for board in self._boards:
            for pin in board.pins:
                yield board, pin

    def as_dict(self):
        meta = self.user.as_dict()
        meta['boards'] = [
            board.as_dict() for board in self._boards
        ]
        return meta

    def save_meta(self, file_name):
        meta = self.as_dict()
        json.dump(meta, open(file_name, "wb"))
