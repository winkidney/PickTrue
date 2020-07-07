import click

from picktrue.sites.douban import DoubanPersonalAlbum
from picktrue.sites.pixiv import Pixiv

from picktrue.logger import download_logger
from picktrue.sites.artstation import ArtStation
from picktrue.sites.huaban import HuaBan, HuaBanBoard
from picktrue.engine import Downloader


@click.group('downloader')
def entry():
    pass


@click.argument("url")
@click.option("--proxy", default=None, type=click.STRING)
@entry.command(
    "artstation-user",
    help='download from artstation user home page',
)
def artstation_user(url, proxy):
    site = ArtStation(url, proxy=proxy)
    downloader = Downloader(fetcher=site.fetcher, save_dir=site.dir_name)
    downloader.add_task(
        site.tasks
    )
    download_logger.info("All task add...waiting for execution...")
    try:
        downloader.join()
    except KeyboardInterrupt:
        download_logger.warn("Exiting...Press crtl+c again to force quit")
        downloader.stop()
        exit(0)
    else:
        download_logger.info("All task done...Enjoy!")


@click.argument("url")
@entry.command(
    "huaban-user",
    help='download from huaban.com user home page',
)
def huban_user(url):
    site = HuaBan(url)
    downloader = Downloader(fetcher=site.fetcher, save_dir=site.dir_name)
    downloader.add_task(
        site.tasks
    )
    download_logger.info("All task add...waiting for execution...")
    try:
        downloader.join()
    except KeyboardInterrupt:
        download_logger.warn("Exiting...Press crtl+c again to force quit")
        downloader.stop()
        exit(0)
    else:
        download_logger.info("All task done...Enjoy!")


@click.argument("url")
@entry.command(
    "huaban-board",
    help='download from huaban.com specified board page',
)
def huban_board(url):
    site = HuaBanBoard(url)
    downloader = Downloader(fetcher=site.fetcher, save_dir=site.dir_name)
    downloader.add_task(
        site.tasks
    )
    download_logger.info("All task add...waiting for execution...")
    try:
        downloader.join()
    except KeyboardInterrupt:
        download_logger.warn("Exiting...Press crtl+c again to force quit")
        downloader.stop()
        exit(0)
    else:
        download_logger.info("All task done...Enjoy!")


@click.option(
    '--proxy',
    help="http/https/socks5 is supported",
    default=None,
)
@click.argument("member-id")
@click.argument("password")
@click.argument("username")
@entry.command(
    "pixiv-member",
    help='download from pixiv.net user home page',
)
def huban_user(member_id, username, password, proxy):
    site = Pixiv(member_id, username, password, proxy=proxy)
    downloader = Downloader(fetcher=site.fetcher, save_dir=site.dir_name)
    downloader.add_task(
        site.tasks
    )
    download_logger.info("All task add...waiting for execution...")
    try:
        downloader.join()
    except KeyboardInterrupt:
        download_logger.warn("Exiting...Press crtl+c again to force quit")
        downloader.stop()
        exit(0)
    else:
        download_logger.info("All task done...Enjoy!")


@click.argument("album-url")
@entry.command(
    "douban-personal-album",
    help='download from douban personal album',
)
def douban_personal_album(album_url):
    site = DoubanPersonalAlbum(album_url)
    downloader = Downloader(fetcher=site.fetcher, save_dir=site.dir_name)
    downloader.add_task(
        site.tasks
    )
    download_logger.info("All task add...waiting for execution...")
    try:
        downloader.join()
    except KeyboardInterrupt:
        download_logger.warn("Exiting...Press crtl+c again to force quit")
        downloader.stop()
        exit(0)
    else:
        download_logger.info("All task done...Enjoy!")


def main():
    entry()


if __name__ == "__main__":
    main()
