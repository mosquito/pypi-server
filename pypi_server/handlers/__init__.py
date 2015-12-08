# encoding: utf-8
import os
from tornado.gen import coroutine, maybe_future, Return
from tornado.web import RedirectHandler, StaticFileHandler
from pypi_server import ROOT
from pypi_server.handlers import base


ROUTES = [
    (r"^/favicon.ico$", RedirectHandler, {'url': '/static/favicon/favicon.ico'}),
    (r"^/static/(.*)$", StaticFileHandler, {'path': os.path.join(ROOT, 'static')})
]


def route(uri, kwargs=None):
    kwargs = kwargs or {}

    def decorator(cls):
        ROUTES.append((uri, cls, kwargs))
        return cls

    return decorator


def add_slash(cls):
    def redirect(self, *args, **kwargs):
        pass

    class WrappedClass(cls):
        @coroutine
        def prepare(self, *args, **kwargs):
            if not self.request.path.endswith('/'):
                raise Return(self.redirect("{0}/".format(self.request.path)))
            else:
                raise Return((yield maybe_future(cls.prepare(self, *args, **kwargs))))

    WrappedClass.__name__ = cls.__name__

    return WrappedClass


from pypi_server.handlers.default import DefaultHandler
import pypi_server.handlers.index
import pypi_server.handlers.pypi
import pypi_server.handlers.api
