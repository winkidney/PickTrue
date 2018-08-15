import tkinter as tk
import webbrowser
from tkinter import ttk

from picktrue.gui.downloader import ArtStation, HuaBan


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
        self.tabs.pack(
            side=tk.LEFT,
        )

    @staticmethod
    def open_online_help():
        url = 'https://github.com/winkidney/PickTrue'
        webbrowser.open_new_tab(url)

    @staticmethod
    def show_about():
        webbrowser.open_new_tab(
            'https://github.com/winkidney/'
        )

    def build_menu(self):
        main_menu = tk.Menu(self)
        self.config(menu=main_menu)
        main_menu.add_cascade(label="在线帮助", command=self.open_online_help)
        main_menu.add_command(label="关于作者", command=self.show_about)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
