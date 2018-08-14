# coding: utf-8
import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox as msgbox

from picktrue.gui.entry import art_station_run
from picktrue.utils import run_as_thread


def info(message, title="信息"):
    msgbox.showinfo(title=title, message=message)


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

    def set_label(self, text):
        self.text.set(text)

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


class Downloader(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.downloader = None

        self.build_menu()
        self.title("PickTrue 图站下载器(目前仅支持ArtStation)")

        self.url = NamedInput(self, name="用户主页")
        self.save_path = FileBrowse(self)

        self.start_btn = ttk.Button(
            text="开始下载",
            command=self.start_download,
        )
        self.stop_btn = ttk.Button(
            text="停止下载",
            command=self.stop_download,
        )
        self.start_btn.pack(fill=tk.BOTH, expand=1)
        self.stop_btn.pack(fill=tk.BOTH, expand=1)

        self.progress = ttk.Progressbar(
            self,
            orient="horizontal",
            length=600,
            mode="determinate",
        )
        self.progress.pack(expand=1)
        self.status = StatusBar(self)
        self.start_update()

    def start_download(self):
        url = self.url.get_input()
        path_prefix = self.save_path.get_path()
        if not url:
            return info("用户主页是必填的")
        if not path_prefix:
            return info("下载文件夹不能为空")
        if self.downloader is not None:
            if not self.downloader.done:
                return info("请停止后再重新点击下载...")
        self.downloader = art_station_run(
            url=url,
            path_prefix=path_prefix,
        )

    def stop_download(self):
        if self.downloader is not None:
            self.downloader.stop()
            self.downloader = None

    @staticmethod
    def show_about():
        info("作者：https://github.com/winkidney/")

    def build_menu(self):
        menu = tk.Menu(self)
        self.config(menu=menu)
        main_menu = tk.Menu(menu)

        # adds a command to the menu option, calling it exit, and the
        # command it runs on event is client_exit
        main_menu.add_command(label="关于", command=self.show_about)
        menu.add_cascade(label="帮助", menu=main_menu)

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
            self.progress['value'] = 0
            self.progress['maximum'] = 100
            self.status.set("")
        else:
            self.progress["value"] = self.downloader.counter.done
            self.progress['maximum'] = self.downloader.counter.total
            msg = self.downloader.counter.format()
            if self.downloader.done:
                msg = msg + "  全部下载完毕，可以开始新的下载了：）"
            self.status.set(msg)


def run():
    app = Downloader()
    app.mainloop()


if __name__ == "__main__":
    run()
