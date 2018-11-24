from collections import namedtuple
from typing import NamedTuple


# requires python >= 3.6.1
class ImageItem(NamedTuple):
    url: str
    name: str or function
    meta: dict = None


DownloadTaskItem = namedtuple(
    'TaskItem',
    (
        'image',
        'base_save_path',
    )
)


UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
