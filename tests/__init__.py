import os
from pypi_server.handlers.base import BaseHandler
from tempfile import NamedTemporaryFile
from pypi_server.db import init_db, DB
from tornado.testing import AsyncHTTPTestCase
from pypi_server.server import create_app
from rest_client.async import RESTClient
from tornado.testing import gen_test
from tornado.httpclient import HTTPRequest, HTTPError
from tornado.concurrent import futures
from tornado.gen import Return, coroutine
import logging


BaseHandler.THREAD_POOL = futures.ThreadPoolExecutor(2)


class TestCase(AsyncHTTPTestCase):
    def setUp(self):
        super(TestCase, self).setUp()

        # Init DB
        self.__db_file = NamedTemporaryFile(mode="r+")

        logging.getLogger("peewee").setLevel(logging.WARNING)
        init_db("sqlite://{0}".format(self.__db_file.name))
        logging.getLogger("peewee").setLevel(logging.DEBUG)

    def get_app(self):
        return create_app(
            secret=os.urandom(32),
            io_loop=self.io_loop,
        )

    def get_rest_client(self):
        return RESTClient(self.io_loop, self.http_client)

    def tearDown(self):
        DB.close()
        self.__db_file.close()

        super(TestCase, self).tearDown()


__all__ = (
    "gen_test",
    "TestCase",
    "HTTPRequest",
    "HTTPError",
    "Return",
    "coroutine"
)
