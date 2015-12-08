# encoding: utf-8
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from tornado.log import app_log as log
from tornado.web import HTTPError
from pypi_server.handlers.base import BaseHandler, threaded


try:
    import ujson as json
except ImportError:
    import json


class JSONHandler(BaseHandler):
    _json = None

    @coroutine
    def prepare(self, *args, **kwargs):
        content_type = self.request.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            raise HTTPError(400)

        if self.request.method.upper() in ('POST', 'PUT'):
            self._json = yield self.thread_pool.submit(self._from_json, self.request.body)
        else:
            self._json = None

    @classmethod
    @threaded
    def _to_json(cls, data):
        return json.dumps(data)

    def _on_async_response_fail(self, result):
        if isinstance(result, Exception):
            log.exception(result)
            if not self._finished:
                self.send_error(500)

    def response(self, data):
        self.set_header('Content-Type', 'application/json')
        self._auto_finish = False
        IOLoop.current().add_future(
            self._async_response(data),
            self._on_async_response_fail
        )

    @coroutine
    def _async_response(self, data):
        if not self._finished:
            self.finish((yield self._to_json(data)))

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
