#!/usr/bin/env python
# encoding: utf-8
import datetime
from functools import wraps


class HTTPCache(object):
    def __init__(self, timeout, use_expires=False, expire_timeout=60):
        self.timeout = timeout
        self.expire_timeout = expire_timeout
        self.use_expires = use_expires

    def __call__(self, func):
        @wraps(func)
        def wrap(handler, *args, **kwargs):
            ret = func(handler, *args, **kwargs)
            self.set_cache(handler)
            return ret

        return wrap

    def set_cache(self, handler, **kwargs):
        if hasattr(handler, '_new_cookie') and handler._new_cookie:
            return

        if handler._status_code == 200:
            if handler.request.method == "GET" and kwargs.get('timeout', self.timeout):
                handler.set_header("X-Accel-Expires", kwargs.get('timeout', self.timeout))

            if kwargs.get('use_expires', self.use_expires):
                handler.set_header(
                    "Expires",
                    (datetime.datetime.now() + datetime.timedelta(
                        seconds=kwargs.get('expire_timeout', self.expire_timeout)
                    )).strftime("%a, %d %b %Y %H:%M:%S %Z")
                )
                handler.set_header(
                    "Cache-Control",
                    "max-age={0}".format(kwargs.get('expire_timeout', self.expire_timeout))
                )