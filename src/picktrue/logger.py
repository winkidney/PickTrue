import logging
import sys

def __get_logger(name):
    __log_level = logging.INFO

    if "--debug-%s" % name in sys.argv:
        __log_level = logging.DEBUG

    fmt = "%(levelname)s - %(asctime)-15s - %(filename)s - line %(lineno)d --> %(message)s"
    date_fmt = "%a %d %b %Y %H:%M:%S"
    formatter = logging.Formatter(fmt, date_fmt)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(
        handler
    )
    logger.setLevel(level=__log_level)
    return logger


download_logger = __get_logger('download')


__all__ = (
    'download_logger',
)
