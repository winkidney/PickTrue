# coding: utf-8
import platform

import os
import tkinter as tk
from tkinter import filedialog, messagebox as msgbox, ttk


def info(message, title="信息"):
    msgbox.showinfo(title=title, message=message)


def open_sys_explorer(path):
    ptf = platform.system().lower()
    if "darwin" in ptf:
        return os.system('open %s' % path)
    elif 'windows' in ptf:
        return os.system('explorer %s' % path)
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
        label = tk.Label(self, text=name)
        label.pack(side=tk.LEFT)

        self.entry = tk.Entry(self)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=1)
        self.pack(fill=tk.X)

    def get_input(self):
        return self.entry.get()


class FileBrowse(tk.Frame):

    def __init__(self, master=None, **kwargs):
        super(FileBrowse, self).__init__(master=master, **kwargs)
        self.label_text = tk.StringVar()
        btn = tk.Button(self, text="下载到", command=self.choose_file)
        btn.pack(
            side=tk.LEFT,
        )

        tk.Label(self, textvariable=self.label_text).pack(
            side=tk.LEFT,
            fill=tk.X,
        )
        self.pack(fill=tk.X)

        self.label_text.set(
            get_working_dir()
        )

    def choose_file(self):
        path = filedialog.askdirectory(
            title="选择下载文件夹",
        )
        if not path:
            return
        self.label_text.set(path)

    def get_path(self):
        return self.label_text.get()


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
