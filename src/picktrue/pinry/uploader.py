# coding: utf-8

from urllib.parse import urljoin

import requests


class Uploader:
    def __init__(self, pinry_url, username, password):
        """
        @:param: pinry_url, like https://pin.xxx.com/
        """
        self.pinry_url = pinry_url
        self._api_prefix = urljoin(pinry_url, '/api/v2/')
        self._login_url = urljoin(self._api_prefix, 'profile/login/')
        self._pin_creation_url = urljoin(self._api_prefix, 'pins/')
        self._board_add_url = urljoin(self._api_prefix, 'boards/')
        self._board_list_url = urljoin(self._api_prefix, 'boards-auto-complete/')
        self._cached_boards = None
        self.session = requests.session()
        self.login(username, password)

    def _get_board_url(self, board_name):
        board_id = self._get_board_id(board_name)
        return f'{self._board_add_url}{board_id}/'

    def _get_board_id(self, board_name):
        return self.boards[board_name]

    def create_boards(self, board_names: list):
        for name in board_names:
            self.post(self._board_add_url, json={"name": name})

    @property
    def boards(self):
        if self._cached_boards is not None:
            return self._cached_boards
        data = self.session.get(self._board_list_url).json()
        self._cached_boards = {}
        for board in data:
            self._cached_boards[board['name']] = board['id']
        return self._cached_boards

    def _get_csrf_token(self):
        csrf_token = self.session.cookies.get('csrftoken')
        if not csrf_token:
            self.session.get(self._api_prefix)
        csrf_token = self.session.cookies.get('csrftoken')
        headers = {
            'X-CSRFToken': csrf_token,
        }
        return headers

    def patch(self, url, json=None):
        headers = self._get_csrf_token()
        return self.session.patch(
            url=url,
            json=json,
            headers=headers,
        )

    def post(self, url, json=None):
        headers = self._get_csrf_token()
        return self.session.post(
            url=url,
            json=json,
            headers=headers,
        )

    def login(self, username, password):
        data = {
            'username': username,
            'password': password,
        }
        resp = self.post(url=self._login_url, json=data)
        assert resp.status_code == 200

    def create(self, description, referer, url, board_name, tags):
        board_url = self._get_board_url(board_name)
        data = dict(
            description=description,
            referer=referer,
            url=url,
            tags=tags,
        )
        resp = self.post(
            url=self._pin_creation_url,
            json=data,
        )
        if resp.status_code != 201:
            raise ValueError("Failed to create pin %s" % resp.content)
        pin = resp.json()
        pin_id = pin['id']
        resp = self.patch(
            url=board_url,
            json={'pins_to_add': [pin_id, ]}
        )
        assert resp.status_code == 200


def from_csv(path='hi.csv'):
    import csv
    with open(path, 'r') as csv_file:
        reader = csv.DictReader(csv_file, delimiter="|")
        rows = list(reader)
        for row in rows:
            row['tags'] = eval(row['tags'])
        return rows


def to_csv(row_dicts, path='hello.csv'):
    import csv
    fields_names = ['description', 'referer', 'url', 'board_name', 'tags']
    with open(path, 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields_names, delimiter="|")
        writer.writeheader()
        for row in row_dicts:
            writer.writerow(
                row,
            )
