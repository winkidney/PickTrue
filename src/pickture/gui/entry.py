import os

from pickture.engine import Downloader

from pickture.sites.artstation import ArtStation


def art_station_run(url, path_prefix=None):
    site = ArtStation(url)
    path = site.dir_name
    if path_prefix is not None:
        path = os.path.join(path)

    downloader = Downloader(save_dir=path)
    downloader.add_task(
        site.tasks,
        background=True,
    )
    downloader.join(background=True)
    return downloader
