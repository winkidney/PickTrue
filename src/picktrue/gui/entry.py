import os

from picktrue.engine import Downloader

from picktrue.sites.artstation import ArtStation
from picktrue.sites.huaban import HuaBan


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


def art_station_run(url, path_prefix=None):
    site = ArtStation(url)
    return _user_home_run(site, path_prefix=path_prefix)


def hua_ban_run(url, path_prefix=None):
    site = HuaBan(url)
    return _user_home_run(site=site, path_prefix=path_prefix)
