# encoding: utf-8
import logging
from functools import wraps
from time import time
from concurrent.futures import Future


log = logging.getLogger(__name__)


def timeit(func):
    def log_result(start_time):
        log.debug(
            'Time of execution function "%s": %0.6f',
            ".".join(filter(
                None,
                (
                    func.__module__,
                    func.__class__.__name__ if hasattr(func, '__class__') else None,
                    func.__name__
                )
            )),
            time() - start_time
        )

    @wraps(func)
    def wrap(*args, **kwargs):
        start_time = time()

        result = func(*args, **kwargs)
        if isinstance(result, Future):
            result.add_done_callback(lambda x: log_result(start_time))
        else:
            log_result(start_time)

        return result

    return wrap
