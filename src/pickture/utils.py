from threading import Thread


def run_as_thread(func, *args, name=None, **kwargs):
    if name is None:
        name = func.__name__
    t = Thread(target=func, args=args, kwargs=kwargs, name=name)
    t.setDaemon(True)
    t.start()
    return t
