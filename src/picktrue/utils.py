import os
import time

from functools import wraps
from picktrue.logger import pk_logger

from threading import Thread


def run_as_thread(func, *args, name=None, **kwargs):
    if name is None:
        name = func.__name__
    t = Thread(target=func, args=args, kwargs=kwargs, name=name)
    t.setDaemon(True)
    t.start()
    return t


def retry(max_retries=3):

    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                retries += 1
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if retries > max_retries:
                        pk_logger.exception("Error occurs while execute function\n")
                        break
                    time.sleep(1)
            return None
        return wrapped

    return wrapper


def convert2kb(size_in_bytes):
    """ Convert the size from bytes to other units like KB, MB or GB"""
    return size_in_bytes / 1024


def get_file_size_kb(file_name):
    """ Get file in size in given unit like KB, MB or GB"""
    size = os.path.getsize(file_name)
    return convert2kb(size)
