# coding: utf-8

from urllib.parse import urljoin

import requests

from picktrue.logger import pk_logger


class Uploader:
    def __init__(self, pinry_url, username, password, login=False):
        """
        @:param: pinry_url, like https://pin.xxx.com/
        """
        self.pinry_url = pinry_url
        self._api_prefix = urljoin(pinry_url, '/api/v2/')
        self._login_url = urljoin(self._api_prefix, 'profile/login/')
        self._pin_creation_url = urljoin(self._api_prefix, 'pins/')
        self._image_creation_url = urljoin(self._api_prefix, 'images/')
        self._board_add_url = urljoin(self._api_prefix, 'boards/')
        self._board_list_url = urljoin(self._api_prefix, 'boards-auto-complete/')
        self._cached_boards = None
        self.session = requests.session()
        self._username = username
        self._password = password
        if login:
            self.login()

    def _get_board_url(self, board_name):
        board_id = self._get_board_id(board_name)
        return f'{self._board_add_url}{board_id}/'

    def _get_board_id(self, board_name):
        return self.boards[board_name]

    def create_boards(self, board_names: set):
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

    def post(self, url, json=None, files=None):
        headers = self._get_csrf_token()
        if files is None:
            return self.session.post(
                url=url,
                json=json,
                headers=headers,
            )
        else:
            return self.session.post(
                url=url,
                headers=headers,
                files=files,
            )

    def login(self):
        data = {
            'username': self._username,
            'password': self._password,
        }
        resp = self.post(url=self._login_url, json=data)
        return resp.status_code == 200

    def _upload_image(self, file_path):
        resp = self.post(
            self._image_creation_url,
            files={"image": open(file_path, "rb")},
        )
        if resp.status_code != 201:
            raise ValueError(
                "Failed to upload image [%s]: %s" % (
                    file_path,
                    resp.json(),
                )
            )
        return resp.json()['id']

    def _create_pin(self, data, board_name):
        board_url = self._get_board_url(board_name)
        resp = self.post(
            url=self._pin_creation_url,
            json=data,
        )
        if resp.status_code != 201:
            raise ValueError("Failed to create pin %s, %s" % (data, resp.content))
        pin = resp.json()
        pin_id = pin['id']
        resp = self.patch(
            url=board_url,
            json={'pins_to_add': [pin_id, ]}
        )
        if resp.status_code != 200:
            pk_logger.error(
                "Failed to add pin to board: %s, %s" % (board_name, pin)
            )

    def create_with_file_upload(self, description, referer, file_path, board_name, tags):
        image_id = self._upload_image(file_path)
        data = dict(
            description=description,
            referer=referer,
            tags=tags,
            image_by_id=image_id,
        )
        return self._create_pin(
            data,
            board_name,
        )

    def create(self, description, referer, url, board_name, tags):
        data = dict(
            description=description,
            referer=referer,
            url=url,
            tags=tags,
        )
        return self._create_pin(
            data,
            board_name,
        )
