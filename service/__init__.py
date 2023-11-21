import logging as logger
import os
import threading
format = "%(asctime)s: %(message)s"
logger.basicConfig(format=format, level=logger.INFO,
                   datefmt="%H:%M:%S")


class Logger():
    def info(self, content):
        if not os.environ.get(
                "LOGGING_ENABLED", "True") == "True":
            return
        logger.info(content)


logging = Logger()


class Thread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        threading.Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        # print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args,
                                        **self._kwargs)

    def join(self, *args):
        threading.Thread.join(self, *args)
        return self._return
