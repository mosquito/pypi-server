# encoding: utf-8
import hashlib
import logging
from copy import copy
from slimurl import URL
from tornado.gen import coroutine, Return
from tornado.httpclient import AsyncHTTPClient
from tornado.ioloop import IOLoop
from tornado.locks import Lock
from tornado_xmlrpc.client import ServerProxy
from pypi_server.cache import Cache, HOUR, MONTH
from pypi_server.hash_version import HashVersion


log = logging.getLogger(__name__)


def normalize_package_name(name):
    return name.lower().replace("_", "-")


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
    @Cache(HOUR, files_cache=True, ignore_self=True)
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
    @Cache(4 * HOUR, files_cache=True, ignore_self=True)
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

        releases = yield cls.releases(real_name)
        if not releases:
            raise Return(False)

        raise Return(True)

    @classmethod
    @coroutine
    def find_real_name(cls, name):
        name = normalize_package_name(name)

        packages = yield cls.packages()
        real_name = packages.get(name.lower())

        if real_name is None:
            raise LookupError("Package not found")

        raise Return(real_name)

    @classmethod
    @coroutine
    @Cache(4 * HOUR, files_cache=True, ignore_self=True)
    def releases(cls, name):
        process_versions = lambda x: set(map(HashVersion, x))

        all_releases, current_releases = yield [
            cls.XMLRPC.package_releases(name, True),
            cls.XMLRPC.package_releases(name)
        ]

        all_releases = process_versions(all_releases)
        current_releases = process_versions(current_releases)

        hidden_releases = all_releases - current_releases

        res = []
        for x in current_releases:
            x.hidden = False
            res.append(x)

        for x in hidden_releases:
            x.hidden = True
            res.append(x)

        raise Return(set(res))

    @classmethod
    @coroutine
    @Cache(MONTH, files_cache=True, ignore_self=True)
    def release_data(cls, name, version):
        info, files = yield [
            cls.XMLRPC.release_data(str(name), str(version)),
            cls.XMLRPC.release_urls(str(name), str(version))
        ]

        download_url = info.get('download_url')
        if download_url and not files:
            try:
                url = URL(download_url)
                filename = url.path.split('/')[-1]

                if "#" in filename:
                    filename = filename.split("#")[0]

                response = yield cls.CLIENT.fetch(download_url)

                files = [{
                    'filename': filename,
                    'md5_digest': hashlib.md5(response.body).hexdigest(),
                    'downloads': -1,
                    'url': download_url,
                    'size': len(response.body),
                    'comment_text': None,
                }]
            except Exception as e:
                files = []
                log.error("Error when trying to download version %s of package %s", version, name)
                log.exception(e)

        else:
            files = sorted(
                files,
                key=lambda x: x['filename']
            )

        raise Return((info, files))
