from concurrent.futures.thread import ThreadPoolExecutor
from threading import Lock

from picktrue.logger import pk_logger
from picktrue.pinry.ds import from_csv
from picktrue.pinry.uploader import Uploader


class PinryImporter:
    _counter_lock = Lock()

    def __init__(self, base_url, username, password):
        self._base_url = base_url
        self._username = username
        self._password = password
        self.total_pins = 999
        self.done_pins = 0
        self.error_pins = 0
        self._started = False
        self._creating_boards = False
        self._executor = ThreadPoolExecutor(
            max_workers=1,
        )

    def test_login(self):
        uploader = Uploader(
            self._base_url,
            self._username,
            self._password,
        )
        return uploader.login()

    def is_done(self):
        return self.done_pins + self.error_pins == self.total_pins

    def status_text(self):
        if not self._started:
            return "待命..."
        if self.is_done():
            return "导入完毕，可以开始新的导入; 总量: %s,出错: %s, 已完成: %s" % (
                self.total_pins, self.error_pins, self.done_pins,
            )
        else:
            if self._creating_boards:
                return "创建画板..."
            else:
                return "执行中，等待更新；总量: %s,出错: %s, 已完成: %s" % (
                    self.total_pins, self.error_pins, self.done_pins,
                )

    def create_single_pin(self, uploader, pin):
        try:
            if pin.image_url2download is not None:
                uploader.create(
                    pin.description,
                    pin.referer,
                    pin.image_url2download,
                    board_name=pin.board,
                    tags=pin.tags,
                )
            elif pin.file_abs_path is not None:
                uploader.create_with_file_upload(
                    pin.description,
                    pin.referer,
                    file_path=pin.file_abs_path,
                    board_name=pin.board,
                    tags=pin.tags,
                )
        except ValueError:
            pk_logger.exception(
                "Failed to to pin creation:",
            )
            with self._counter_lock:
                self.error_pins += 1
        else:
            with self._counter_lock:
                self.done_pins += 1

    def do_import(self, file_path):
        uploader = Uploader(
            self._base_url,
            self._username,
            self._password,
            login=True,
        )
        pins = from_csv(file_path)
        self._started = True
        self._creating_boards = True
        uploader.create_boards(
            set([pin.board for pin in pins])
        )
        self._creating_boards = False
        self.total_pins = len(pins)
        jobs = []
        for pin in pins:
            job = self._executor.submit(
                self.create_single_pin,
                uploader,
                pin,
            )
            jobs.append(job)
        self._executor.shutdown(wait=True)


