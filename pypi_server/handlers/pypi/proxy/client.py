#!/usr/bin/env python
# encoding: utf-8
import logging
from copy import copy
from tornado.gen import coroutine, Return
from tornado.httpclient import AsyncHTTPClient
from tornado.ioloop import IOLoop
from tornado.locks import Lock
from tornado_xmlrpc.client import ServerProxy
from ....cache import Cache
from ....hash_version import HashVersion

log = logging.getLogger(__name__)


class PYPIClient(object):
    CLIENT = None
    BACKEND = None
    THREAD_POOL = None
    INDEX = None
    XMLRPC = None
    LOCK = None

    @classmethod
    def configure(cls, backend, thread_pool):
        cls.CLIENT = AsyncHTTPClient(io_loop=IOLoop.current())
        cls.BACKEND = backend
        cls.THREAD_POOL = thread_pool
        cls.XMLRPC = ServerProxy(
            str(copy(backend)(path="/pypi")),
        )
        cls.LOCK = Lock()

    @classmethod
    @coroutine
    @Cache(600)
    def packages(cls):
        with (yield cls.LOCK.acquire()):
            index = dict(
                map(
                    lambda x: (x.lower().replace("_", "-"), x),
                    (yield cls.XMLRPC.list_packages())
                )
            )

            log.info("Remote PYPI index updated: %d packages", len(index))
            raise Return(index)

    @classmethod
    @coroutine
    @Cache(600)
    def search(cls, names, descriptions, operator="or"):
        assert operator in ('or', 'and')
        result = yield cls.XMLRPC.search({'name': names, 'description': descriptions}, operator)
        raise Return(result)

    @classmethod
    @coroutine
    def exists(cls, name):
        try:
            real_name = yield cls.find_real_name(name)
        except LookupError:
            raise Return(False)

        releases = yield cls.get_releases(real_name)
        if not releases:
            raise Return(False)

        raise Return(True)

    @classmethod
    @coroutine
    def find_real_name(cls, name):
        name = name.lower().replace("_", "-")

        packages = yield cls.packages()
        real_name = packages.get(name.lower())

        if real_name is None:
            raise LookupError("Package not found")

        raise Return(real_name)

    @classmethod
    @coroutine
    @Cache(600)
    def get_releases(cls, pkg_name):
        raise Return((yield cls.XMLRPC.package_releases(pkg_name)))

    @classmethod
    @coroutine
    @Cache(3600)
    def releases(cls, name):
        raise Return(set(map(HashVersion, (yield cls.XMLRPC.package_releases(name)))))

    @classmethod
    @coroutine
    @Cache(3600)
    def release_data(cls, name, version):
        info = yield cls.XMLRPC.release_data(str(name), str(version))
        raise Return(info)

    @classmethod
    @coroutine
    @Cache(3600)
    def release_files(cls, name, version):
        info = yield cls.XMLRPC.release_urls(str(name), str(version))

        @coroutine
        def fetcher(x):
            raise Return((x, (yield cls.CLIENT.fetch(x['url']))))

        info = yield list(map(fetcher, info))

        ret = []
        for item, response in info:
            item['file'] = response
            ret.append(item)

        raise Return(sorted(ret, key=lambda x: x['filename']))
