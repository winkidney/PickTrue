import json
import re
from json import JSONDecodeError
from pprint import pformat

import os

import random
import string
from collections import namedtuple
from urllib.parse import urljoin

from picktrue.logger import pk_logger
from picktrue.meta import ImageItem, DownloadTaskItem
from picktrue.pinry.ds import Pin2Import, write_to_csv
from picktrue.sites.abstract import DummySite, DummyFetcher
from picktrue.utils import retry

IMAGE_URL_TPL = "http://img.hb.aicdn.com/{file_key}"
BASE_URL = "http://huaban.com"

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
    )
)


class HuaBanFetcher(DummyFetcher):

    def __init__(self):
        super(HuaBanFetcher, self).__init__()
        self.session.headers.update(
            XHR_HEADERS,
        )

    @classmethod
    def get_save_path(cls, task_item):
        save_path = os.path.join(
            task_item.base_save_path,
            task_item.image.meta['board_name'],
        )
        cls.ensure_dir(dir_path=save_path)
        save_path = os.path.join(
            save_path,
            task_item.image.name,
        )
        save_path = cls._safe_path(save_path)
        return save_path

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
            try:
                resp.json()
            except JSONDecodeError:
                pk_logger.error(
                    "Failed to convert resp to json for url {}: {}".format(
                        url,
                        resp.text,
                    )
                )
                raise
        return resp

    @staticmethod
    def ensure_dir(dir_path):
        return os.makedirs(dir_path, exist_ok=True)

    def save(self, content, task_item: DownloadTaskItem):
        """
        :type content: bytearray
        :type task_item: picktrue.meta.TaskItem
        """
        if task_item.image.meta is None:
            return super(HuaBanFetcher, self).save(content, task_item)
        save_path = self.get_save_path(task_item)
        with open(save_path, "wb") as f:
            f.write(content)
        pin2import = mk_pin2import(task_item)
        if pin2import:
            write_to_csv(pin2import, base_path=task_item.base_save_path)


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
            "file_name": file_name,
            "tags": info['tags'],
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


def mk_pin2import(task_item: DownloadTaskItem) -> Pin2Import or None:
    if task_item.image.meta is None:
        return None
    meta = task_item.image.pin_meta
    return Pin2Import(
        referer=meta['link'],
        tags=meta['tags'],
        description=meta['title'],
        board=task_item.image.meta['board_name'],
        file_abs_path=HuaBanFetcher.get_save_path(task_item),
        image_url2download="",
    )


class Board(object):
    def __init__(self, board_url_or_id):
        board_id = str(board_url_or_id)
        self.fetcher = HuaBanFetcher()
        if "http" in board_id:
            board_id = re.findall(r'boards/(\d+)/', board_id)[0]
        self.id = board_id
        path = "/boards/{board_id}/".format(
            board_id=board_id,
        )
        self.base_url = urljoin(BASE_URL, path)
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
        self._init_board()

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

    _init_board = _fetch_home

    def _fetch_further(self, prev_pins):
        if len(prev_pins) == 0:
            info = (
                "prev_pins should not be [], "
                "board: %s, "
                "url: %s, "
                "pin_count: %s, "
                "current_pins: %s, "
            )
            pk_logger.error(
                info% (
                    self.title,
                    self.base_url,
                    self.pin_count,
                    pformat(self._pins),
                )
            )
            return []
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

    def _fetch_pins(self):
        assert len(self._pins) == 0
        self._pins.extend(self._fetch_home())
        for pin in self._pins:
            yield pin
        while self.pin_count > len(self._pins):
            further_pins = self._fetch_further(self._pins)
            if len(further_pins) <= 0:
                break
            self._pins.extend(further_pins)
            for pin in further_pins:
                yield pin

    @property
    def pins(self):
        yield from self._fetch_pins()

    def as_dict(self):
        return {
            "pins": self._pins,
            "title": self.title,
            "description": self.description,
            "pin_count": self.pin_count,
        }


def mk_pin(pin_meta):
    url = pin_meta["url"]
    filename = u"{title}.{ext}".format(
        title=pin_meta['pin_id'],
        ext=pin_meta['ext'],
    )
    return Pin(
        url=url,
        filename=filename,
    )


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
        self._boards_metas = []
        self._init_profile()

    def _fetch_home(self):
        resp = self.fetcher.get(self.base_url, require_json=True)
        user_meta = resp.json()['user']
        self.username = user_meta['username']
        self.board_count = user_meta['board_count']
        self.pin_count = user_meta['pin_count']
        return get_boards(user_meta)

    _init_profile = _fetch_home

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
        assert len(self._boards_metas) == 0
        self._boards_metas.extend(self._fetch_home())
        further_boards = self._boards_metas
        while True:
            for meta in further_boards:
                yield Board(meta['board_id'])
            if self.board_count > len(self._boards_metas):
                further_boards = self._fetch_further(self._boards_metas)
                self._boards_metas.extend(further_boards)
            else:
                break

    @property
    def boards(self):
        """
        :rtype: iter[Board]
        """
        yield from self._fetch_boards()

    def as_dict(self):
        return {
            "username": self.username,
            "board_count": self.board_count,
            "boards": self.boards,
        }


class HuaBan(DummySite):

    fetcher = HuaBanFetcher()

    def __init__(self, user_url):
        self.meta = None
        self.base_url = user_url
        self.user = User(user_url)
        self._boards = []

    @property
    def dir_name(self):
        return self.user.username

    @property
    def tasks(self):
        for board, pin_meta in self._boards_pins:
            pin_item = mk_pin(
                pin_meta
            )
            yield ImageItem(
                url=pin_item.url,
                name=pin_item.filename,
                meta={
                    'board_name': board.title,
                },
                pin_meta=pin_meta,
            )

    @property
    def _boards_pins(self):
        for board in self.user.boards:
            self._boards.append(board)
            for pin in board.pins:
                yield board, pin

    def as_dict(self):
        meta = self.user.as_dict()
        meta['boards'] = [
            board.as_dict() for board in self._boards
        ]
        return meta


class HuaBanBoard(DummySite):

    fetcher = HuaBanFetcher()

    def __init__(self, board_url):
        self.base_url = board_url
        self._board = Board(self.base_url)

    @property
    def dir_name(self):
        return _safe_file_name(
            "%s-%s" % (self._board.title, self._board.id)
        )

    @property
    def tasks(self):
        for pin_meta in self._board.pins:
            pin_item = mk_pin(
                pin_meta
            )
            yield ImageItem(
                url=pin_item.url,
                name=pin_item.filename,
                pin_meta=pin_meta,
            )
