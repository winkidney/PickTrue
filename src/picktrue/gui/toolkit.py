# coding: utf-8
import platform

import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox as msgbox, ttk

from picktrue.gui.config import ConfigStore, config_store


def info(message, title="信息"):
    msgbox.showinfo(title=title, message=message)


def open_sys_explorer(path):
    ptf = platform.system().lower()
    path = Path(path)
    if "darwin" in ptf:
        return os.system('open %s' % path)
    elif 'windows' in ptf:
        return os.system('explorer.exe "%s"' % path)
    elif 'linux' in ptf:
        return os.system('xdg-open %s' % path)
    return info('平台不支持')


def get_working_dir():
    return os.getcwd()


class StatusBar(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.variable=tk.StringVar()
        self.label=tk.Label(
            self, bd=1, relief=tk.SUNKEN, anchor=tk.W,
            textvariable=self.variable,
            font=('arial', 16, 'normal')
        )
        self.variable.set('')
        self.label.pack(fill=tk.X)
        self.pack(fill=tk.BOTH)

    def set(self, value):
        self.variable.set(value)


class NamedInput(tk.Frame):
    def __init__(self, master=None, name=None, **kwargs):
        super(NamedInput, self).__init__(master=master, **kwargs)
        assert name is not None
        self._name = name
        label = tk.Label(self, text=name)
        label.pack(side=tk.LEFT)

        self.entry = tk.Entry(self)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=1)
        self.pack(fill=tk.X)

    def get_input(self):
        return self.entry.get()

    def assert_no_error(self):
        text = self.get_input()
        if not text:
            info(
                "%s 不能为空" % self._name
            )
            raise ValueError("value error, can't be null")


class PasswordInput(tk.Frame):
    def __init__(self, master=None, name=None, **kwargs):
        super(PasswordInput, self).__init__(master=master, **kwargs)
        assert name is not None
        self._name = name
        label = tk.Label(self, text=name)
        label.pack(side=tk.LEFT)

        self.entry = tk.Entry(self, show="*")
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=1)
        self.pack(fill=tk.X)

    def get_input(self):
        return self.entry.get()

    def assert_no_error(self):
        text = self.get_input()
        if not text:
            info(
                "%s 不能为空" % self._name
            )
            raise ValueError("value error, can't be null")


class ProxyInput(NamedInput):
    def assert_no_error(self):
        value = self.get_input()
        if not value:
            return
        results = [kw in value for kw in ('http', 'https', 'socks5')]
        if not any(results):
            info("代理地址错误")
            raise ValueError("Proxy address error")


class FileBrowse(tk.Frame):

    def __init__(self, master=None, store_name=None, text_label=None, **kwargs):
        super(FileBrowse, self).__init__(master=master, **kwargs)
        self.label_text = tk.StringVar()
        btn = tk.Button(self, text=text_label or "下载到", command=self.choose_file)
        btn.pack(
            side=tk.LEFT,
        )

        tk.Label(self, textvariable=self.label_text).pack(
            side=tk.LEFT,
            fill=tk.X,
        )
        self.pack(fill=tk.X)

        self._store_name = store_name
        if store_name is not None:
            self._config = config_store
            save_path = self._config.op_read_path(store_name) or get_working_dir()
        else:
            self._config = None
            save_path = get_working_dir()

        self.label_text.set(
            save_path
        )

    def ask_path(self):
        return filedialog.askdirectory(
            title="选择下载文件夹",
        )

    def choose_file(self):
        path = self.ask_path()
        if not path:
            return
        path = Path(path)
        self.label_text.set(str(path))
        if self._config is not None:
            self._config.op_store_path(self._store_name, path)

    def get_path(self):
        return self.label_text.get()

    def assert_no_error(self):
        text = self.get_path()
        if not text:
            info(
                "%s 不能为空"
            )
            raise ValueError("Value should not be null")


class FilePathBrowse(FileBrowse):
    def ask_path(self):
        return filedialog.askopenfilename(
            title="选择csv文件",
        )


class ProgressBar(ttk.Progressbar):

    def __init__(self, master=None):
        super(ProgressBar, self).__init__(
            master=master,
            orient="horizontal",
            length=600,
            mode="determinate",
        )
        self.pack(expand=1)

    def update_progress(self, current, maximum=None):
        self['value'] = current
        if maximum is not None:
            self['maximum'] = maximum

    def reset_progress(self):
        self.update_progress(0, 0)
