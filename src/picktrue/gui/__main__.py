import tkinter as tk
from tkinter import ttk

from picktrue.gui.downloader import ArtStation, HuaBan
from picktrue.gui.toolkit import info


class App(tk.Tk):

    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        self.tabs = ttk.Notebook(self)
        self.title("PickTrue - 相册下载器")
        self.build_menu()
        self._art_station = ArtStation(self)
        self._hua_ban = HuaBan(self)
        self.tabs.add(self._art_station, text='ArtStation')
        self.tabs.add(self._hua_ban, text='花瓣网')
        self.tabs.pack()

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


def run():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    run()
