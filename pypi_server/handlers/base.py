# encoding: utf-8
from functools import wraps
from tornado.web import RequestHandler


try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import ujson as json
except ImportError:
    import json


class BaseHandler(RequestHandler):
    _NULL = object()
    THREAD_POOL = None
    STORAGE = None

    @property
    def thread_pool(self):
        return self.THREAD_POOL

    @classmethod
    def threaded(cls, func):
        @wraps(func)
        def wrap(*args, **kwargs):
            return cls.THREAD_POOL.submit(func, *args, **kwargs)

        return wrap

    def get_secure_cookie(self, name, value=None, max_age_days=31, min_version=None):
        val = super(BaseHandler, self).get_secure_cookie(
            name, None, max_age_days=max_age_days, min_version=min_version
        )

        if val is None:
            return value

        return pickle.loads(val) if val else val

    def set_secure_cookie(self, name, value, expires_days=30, version=None, **kwargs):
        return super(BaseHandler, self).set_secure_cookie(
            name, pickle.dumps(value, protocol=2), expires_days=expires_days,
            version=version, **kwargs
        )


threaded = BaseHandler.threaded