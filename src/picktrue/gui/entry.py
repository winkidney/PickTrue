import os

from picktrue.engine import Downloader

from picktrue.sites.artstation import ArtStation
from picktrue.sites.douban import DoubanPersonalAlbum
from picktrue.sites.huaban import HuaBan, HuaBanBoard
from picktrue.sites.pixiv import Pixiv


def _user_home_run(site, path_prefix=None):
    """
    :type site: picktrue.sites.abstract.DummySite
    :type path_prefix: str or None
    """
    path = site.dir_name
    if path_prefix is not None:
        path = os.path.join(path_prefix, path)
    downloader = Downloader(save_dir=path, fetcher=site.fetcher)
    downloader.add_task(
        site.tasks,
        background=True,
    )
    downloader.join(background=True)
    return downloader


def art_station_run(url, path_prefix=None, proxy=None):
    site = ArtStation(url, proxy=proxy)
    return _user_home_run(site, path_prefix=path_prefix)


def hua_ban_run(url, path_prefix=None, return_site=False):
    site = HuaBan(url)
    if return_site:
        return _user_home_run(site=site, path_prefix=path_prefix), site
    else:
        return _user_home_run(site=site, path_prefix=path_prefix)


def hua_ban_board_run(url, path_prefix=None):
    site = HuaBanBoard(url)
    return _user_home_run(site=site, path_prefix=path_prefix)


def douban_personal_album_board_run(url, path_prefix=None):
    site = DoubanPersonalAlbum(url)
    return _user_home_run(site=site, path_prefix=path_prefix)


def pixiv_run(url, username, password, proxy=None, path_prefix=None):
    site = Pixiv(
        url=url,
        username=username,
        password=password,
        proxy=proxy,
    )
    return _user_home_run(site, path_prefix)
