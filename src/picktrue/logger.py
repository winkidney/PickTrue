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
    file_handler = logging.FileHandler(
        "./picktrue.all.log",
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(
        handler
    )
    logger.addHandler(
        file_handler
    )
    logger.setLevel(level=__log_level)
    return logger


pk_logger = __get_logger('picktrue')


__all__ = (
    'pk_logger',
)
