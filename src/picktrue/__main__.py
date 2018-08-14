import click

from picktrue.sites.artstation import ArtStation
from .engine import Downloader


@click.group('artstation')
def artstation():
    pass

@click.argument("url")
@artstation.command("user")
def artstation_user(url):
    site = ArtStation(url)
    downloader = Downloader(save_dir=site.dir_name)
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
    artstation()

if __name__ == "__main__":
    main()

