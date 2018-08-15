import click

from picktrue.sites.artstation import ArtStation
from picktrue.sites.huaban import HuaBan
from .engine import Downloader


@click.group('downloader')
def entry():
    pass


@click.argument("url")
@entry.command(
    "artstation-user",
    help='download from artstation user home page',
)
def artstation_user(url):
    site = ArtStation(url)
    downloader = Downloader(fetcher=site.fetcher, save_dir=site.dir_name)
    downloader.add_task(
        site.tasks
    )
    print("All task add...waiting for execution...")
    try:
        downloader.join()
    except KeyboardInterrupt:
        print("Exiting...Press crtl+c again to force quit")
        downloader.stop()
        exit(0)
    else:
        print("All task done...Enjoy!")


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
    print("All task add...waiting for execution...")
    try:
        downloader.join()
    except KeyboardInterrupt:
        print("Exiting...Press crtl+c again to force quit")
        downloader.stop()
        exit(0)
    else:
        print("All task done...Enjoy!")


def main():
    entry()


if __name__ == "__main__":
    main()
