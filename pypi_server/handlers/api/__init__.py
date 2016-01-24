# encoding: utf-8
import logging
from tornado.gen import coroutine, maybe_future
from tornado.ioloop import IOLoop
from tornado.web import HTTPError
from pypi_server.handlers.base import BaseHandler, threaded


try:
    import ujson as json
except ImportError:
    import json


log = logging.getLogger(__name__)


def split_header(header):
    return dict(
        map(
            lambda x: list(map(lambda y: y.strip('"\''), x.split("=", 1))),
            filter(
                lambda x: "=" in x,
                map(lambda x: x.strip(), header.split(";"))
            )
        )
    )


class JSONHandler(BaseHandler):
    __slots__ = ("_json", "__io_loop")

    @coroutine
    def prepare(self, *args, **kwargs):
        self.__io_loop = IOLoop.current()

        if self.request.method.upper() in ('POST', 'PUT'):
            content_type = self.request.headers.get('Content-Type', '')

            if 'application/json' not in content_type:
                raise HTTPError(415)

            charset = split_header(content_type).get('charset', 'utf-8')

            try:
                self._json = yield self.thread_pool.submit(
                        self._from_json,
                        self.request.body.decode(charset)
                )
            except Exception as e:
                log.exception(e)
                raise HTTPError(415)
        else:
            self._json = None

    @classmethod
    @threaded
    def _to_json(cls, data):
        return json.dumps(data)

    def response(self, data):
        self.set_header('Content-Type', 'application/json')
        self._auto_finish = False

        self.__io_loop.add_callback(self._async_response, data)

    @coroutine
    def _async_response(self, data):
        data = yield maybe_future(data)
        resp = yield self._to_json(data)

        if not self._finished:
            log.debug("Sending: %r", resp)
            self.finish(resp)

    @staticmethod
    def _from_json(data):
        return json.loads(data)

    @property
    def json(self):
        return self._json


import pypi_server.handlers.api.login
import pypi_server.handlers.api.users
import pypi_server.handlers.api.user
import pypi_server.handlers.api.packages
import pypi_server.handlers.api.package
import pypi_server.handlers.api.version
