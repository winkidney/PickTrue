import time

from functools import wraps
from picktrue.logger import download_logger

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
                        download_logger.exception("Error occurs while execute function\n")
                        break
                    time.sleep(1)
            return None
        return wrapped

    return wrapper
