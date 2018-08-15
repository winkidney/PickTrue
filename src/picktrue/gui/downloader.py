# coding: utf-8
import os
import time
import tkinter as tk
from tkinter import ttk

from picktrue.gui.entry import art_station_run, hua_ban_run
from picktrue.gui.toolkit import NamedInput, FileBrowse, StatusBar, info, ProgressBar, open_sys_explorer
from picktrue.utils import run_as_thread


class UserHomeDownloader(tk.Frame):

    def __init__(self, *args, **kwargs):
        super(UserHomeDownloader, self).__init__(*args, **kwargs)

        self.downloader = None
        self.url = NamedInput(self, name="用户主页 ")
        self.save_path = FileBrowse(self)
        self.btn_group = self.build_buttons()
        self.progress = ProgressBar(self)
        self.status = StatusBar(self)
        self.start_update()

    def run(self, url, path_prefix):
        raise NotImplementedError()

    def build_buttons(self):
        btn_args = dict(
            height=1,
        )
        btn_group = tk.Frame(self)

        btns = [
            tk.Button(
                btn_group,
                text="开始下载",
                command=self.start_download,
                **btn_args
            ),
            tk.Button(
                btn_group,
                text="停止下载",
                command=self.stop_download,
                **btn_args,
            ),
            tk.Button(
                btn_group,
                text="打开下载文件夹",
                command=self.open_download_folder,
                **btn_args,
            )
        ]

        for index, btn in enumerate(btns):
            btn.pack(fill=tk.BOTH, expand=1)
            btn.grid(column=index, row=0, sticky=tk.W)

        btn_group.pack(fill=tk.BOTH, expand=1)
        return btn_group

    def open_download_folder(self):
        path = self.save_path.get_path()
        open_sys_explorer(path)

    def start_download(self):
        url = self.url.get_input()
        path_prefix = self.save_path.get_path()
        if not url:
            return info("用户主页是必填的")
        if not path_prefix:
            return info("下载文件夹不能为空")
        if not os.access(path_prefix, os.W_OK):
            return info("对下载文件夹没有写权限，请重新选择")
        if self.downloader is not None:
            if not self.downloader.done:
                return info("请停止后再重新点击下载...")
        self.downloader = self.run(
            url=url,
            path_prefix=path_prefix,
        )

    def stop_download(self):
        if self.downloader is not None:
            self.downloader.stop()
            self.downloader = None

    def start_update(self):
        run_as_thread(self._update_loop)

    def _update_loop(self):
        while True:
            time.sleep(0.1)
            try:
                self.update_progress()
            except AttributeError:
                pass

    def update_progress(self):
        if self.downloader is None:
            self.progress.update_progress(
                0, 100
            )
            self.status.set("")
        else:
            self.progress.update_progress(
                self.downloader.counter.done,
                self.downloader.counter.total,
            )
            msg = self.downloader.counter.format()
            if self.downloader.done:
                msg = msg + "  全部下载完毕，可以开始新的下载了：）"
            self.status.set(msg)


class HuaBan(UserHomeDownloader):

    def run(self, url, path_prefix):
        return hua_ban_run(
            url=url,
            path_prefix=path_prefix,
        )

class ArtStation(UserHomeDownloader):

    def run(self, url, path_prefix):
        return art_station_run(
            url=url,
            path_prefix=path_prefix,
        )
