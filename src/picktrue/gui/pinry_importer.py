import time
import tkinter as tk

from picktrue.gui.toolkit import ProgressBar, StatusBar, NamedInput, FileBrowse, info, FilePathBrowse, PasswordInput
from picktrue.pinry.importer import PinryImporter
from picktrue.utils import run_as_thread


class PinryImporterGUI(tk.Frame):

    title = "导入到Pinry"

    def __init__(self, *args, **kwargs):
        super(PinryImporterGUI, self).__init__(*args, **kwargs)

        self._url = NamedInput(self, name="Pinry部署地址")
        self._username = NamedInput(self, name="用户名")
        self._password = PasswordInput(self, name="密码")
        self._csv_file = FilePathBrowse(self, store_name="import_csv", text_label="CSV文件文件路径")
        self.btn_group = self.build_buttons()
        self._importer = None
        self.progress = ProgressBar(self)
        self.status = StatusBar(self)
        self.start_update()

    def _get_importer(self):
        return PinryImporter(
            base_url=self._url.get_input(),
            username=self._username.get_input(),
            password=self._password.get_input(),
        )

    def build_buttons(self):
        btn_args = dict(
            height=1,
        )
        btn_group = tk.Frame(self)

        buttons = [
            tk.Button(
                btn_group,
                text=text,
                command=command,
                **btn_args
            )
            for text, command in (
                ("测试登录", self._test_login),
                ("开始导入", self._start_import),
            )
        ]

        for index, btn in enumerate(buttons):
            btn.grid(column=index, row=0, sticky=tk.N)

        btn_group.pack(fill=tk.BOTH, expand=1)
        return btn_group

    def _test_login(self):
        importer = self._get_importer()
        if importer.test_login() is True:
            info("登录成功")
        else:
            info("情检查用户名密码以及部署路径是否可访问")

    def _start_import(self):
        self._importer = self._get_importer()
        run_as_thread(
            self._importer.do_import,
            self._csv_file.get_path(),
            name="import2pinry"
        )

    def start_update(self):
        run_as_thread(self._update_loop)

    def _update_loop(self):
        while True:
            time.sleep(0.1)
            self.update_progress()

    def update_progress(self):
        if self._importer is not None:
            self.progress.update_progress(
                self._importer.done_pins,
                self._importer.total_pins,
            )
            self.status.set(self._importer.status_text())
        else:
            self.progress.update_progress(0, 0)
            self.status.set("待机...")
