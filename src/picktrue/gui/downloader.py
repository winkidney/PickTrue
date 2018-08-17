# coding: utf-8
import os
import time
import tkinter as tk

from picktrue.gui.entry import art_station_run, hua_ban_run, pixiv_run
from picktrue.gui.toolkit import (
    NamedInput, FileBrowse, StatusBar, info, ProgressBar, open_sys_explorer, PasswordInput,
    ProxyInput
)
from picktrue.utils import run_as_thread


def mk_normal_inputs(master=None, store_name=None):
    url = NamedInput(master, name="用户主页 ")
    save_path = FileBrowse(master, store_name=store_name)
    return url, save_path


def mk_pixiv_inputs(master=None):
    url = NamedInput(master, name="要下载的用户主页地址")
    username = NamedInput(master, name="Pixiv账户名（需要登录才能下载）")
    password = PasswordInput(master, name="登录密码")
    proxy = ProxyInput(master, name="代理地址(支持http/https/socks5， 可不填)")
    save_path = FileBrowse(master, store_name="pixiv_save_path")
    return url, username, password, proxy, save_path


class UserHomeDownloader(tk.Frame):

    def __init__(self, *args, store_name=None, **kwargs):
        super(UserHomeDownloader, self).__init__(*args, **kwargs)
        self.downloader = None
        self.url, self.save_path = mk_normal_inputs(self, store_name=store_name)
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

        buttons = [
            tk.Button(
                btn_group,
                text=text,
                command=command,
                **btn_args
            )
            for text, command in (
                ("开始下载", self.start_download),
                ("停止下载", self.stop_download),
                ("打开下载文件夹", self.open_download_folder),
            )
        ]

        for index, btn in enumerate(buttons):
            btn.grid(column=index, row=0, sticky=tk.N)

        btn_group.pack(fill=tk.BOTH, expand=1)
        return btn_group

    def open_download_folder(self):
        path = self.save_path.get_path()
        open_sys_explorer(path)

    def start_download(self):
        self.url.assert_no_error()
        self.save_path.assert_no_error()
        url = self.url.get_input()
        path_prefix = self.save_path.get_path()
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


class Pixiv(tk.Frame):

    def __init__(self, *args, **kwargs):
        super(Pixiv, self).__init__(*args, **kwargs)

        self.downloader = None
        self.url, self.username, self.password, \
            self.proxy, self.save_path = mk_pixiv_inputs(self)
        self.btn_group = self.build_buttons()
        self.progress = ProgressBar(self)
        self.status = StatusBar(self)
        self.start_update()

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
                ("开始下载", self.start_download),
                ("停止下载", self.stop_download),
                ("打开下载文件夹", self.open_download_folder),
            )
        ]

        for index, btn in enumerate(buttons):
            btn.grid(column=index, row=0, sticky=tk.N)

        btn_group.pack(fill=tk.BOTH, expand=1)
        return btn_group

    def open_download_folder(self):
        path = self.save_path.get_path()
        open_sys_explorer(path)

    def start_download(self):
        self.url.assert_no_error()
        self.username.assert_no_error()
        self.password.assert_no_error()
        self.proxy.assert_no_error()
        self.save_path.assert_no_error()

        url = self.url.get_input()
        proxy = self.proxy.get_input() or None
        username = self.username.get_input()
        password = self.password.get_input()
        path_prefix = self.save_path.get_path()

        if not os.access(path_prefix, os.W_OK):
            return info("对下载文件夹没有写权限，请重新选择")
        if self.downloader is not None:
            if not self.downloader.done:
                return info("请停止后再重新点击下载...")
        self.downloader = pixiv_run(
            url=url,
            username=username,
            password=password,
            proxy=proxy,
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

    def __init__(self, *args, **kwargs):
        super(HuaBan, self).__init__(*args, store_name='huaban_save_path', **kwargs)

    def run(self, url, path_prefix):
        return hua_ban_run(
            url=url,
            path_prefix=path_prefix,
        )


class ArtStation(UserHomeDownloader):

    def __init__(self, *args, **kwargs):
        super(ArtStation, self).__init__(*args, store_name='artstation_save_path', **kwargs)

    def run(self, url, path_prefix):
        return art_station_run(
            url=url,
            path_prefix=path_prefix,
        )
