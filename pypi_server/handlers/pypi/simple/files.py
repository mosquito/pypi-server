# encoding: utf-8
import os
import logging

from pypi_server.cache import Cache
from pypi_server.timeit import timeit
from tornado.gen import coroutine, Return
from tornado.ioloop import IOLoop
from tornado.web import HTTPError
from tornado.httpclient import HTTPError as HTTPClientError
from pypi_server.handlers import route, add_slash
from pypi_server.handlers.base import BaseHandler, threaded
from pypi_server.handlers.pypi.proxy.client import PYPIClient
from pypi_server.db.packages import PackageVersion, Package, PackageFile


log = logging.getLogger(__name__)


try:
    xrange
except NameError:
    xrange = range


PACKAGE_META = {
    'author': None,
    'author_email': None,
    'maintainer': None,
    'maintainer_email': None,
    "home_page": None,
    "license": None,
    "summary": None,
    "description": None,
    "keywords": None,
    "platform": None,
    "download_url": None,
    "classifiers": None,
    "requires": None,
    "requires_dist": None,
    "provides": None,
    "provides_dist": None,
    "requires_external": None,
    "requires_python": None,
    "obsoletes": None,
    "obsoletes_dist": None,
    "project_url": None,
}


def chunks(lst, n):
    for i in xrange(0, len(lst), n):
        yield lst[i:i + n]


@coroutine
@timeit
@Cache(3600, files_cache=True)
def proxy_remote_package(package):
    pkg = yield threaded(Package.get_or_create)(name=package, proxy=True)

    releases, cached_releases = yield [PYPIClient.releases(pkg.name), threaded(pkg.versions)(True)]
    IOLoop.current().add_callback(threaded(pkg.hide_versions), filter(lambda x: not x.hidden, releases))

    cached_releases = set(map(lambda x: x.version, cached_releases))
    new_releases = list(releases - cached_releases)

    for release_part in chunks(new_releases, 10):
        yield [release_fetch(pkg, release) for release in release_part]

    raise Return(pkg)


@threaded
@timeit
def release_db_save(package, rel, version_info, release_files):
    version = package.create_version(rel)
    version.fetched = False

    for key, val in PACKAGE_META.items():
        setattr(version, key, version_info.get(val if val else key))

    version.save()

    for f in release_files:
        try:
            pkg_file = version.create_file(f['filename'])
        except Exception as e:
            log.error("Error when trying to download file %s for version %s of package %s", f['filename'], version, package)
            log.exception(e)
            continue
        pkg_file.fetched = False
        pkg_file.url = f['url']
        pkg_file.md5 = f['md5_digest']
        pkg_file.save()

    return version


@timeit
@coroutine
def release_fetch(package, rel):
    try:
        version_info, release_files = yield PYPIClient.release_data(package.name, rel)
        raise Return((yield release_db_save(package, rel, version_info, release_files)))
    except:
        log.exception("Error proccess %r %r", package, rel)


@route(r'/simple/(?P<package>[\w\.\d\-\_]+)/?')
@route(r'/simple/(?P<package>[\w\.\d\-\_]+)/(?P<version>[\w\.\d\-\_]+)/?')
@add_slash
class VersionsHandler(BaseHandler):
    @timeit
    @coroutine
    def get(self, package, version=None):
        exists, is_proxy, pkg = yield self.packages_list(package)

        if not exists or (is_proxy or not pkg):
            try:
                pkg = yield self.proxy_package(package)
            except LookupError:
                pkg = None

        if not pkg:
            raise HTTPError(404)

        files = yield threaded(pkg.files)(version=version)

        if not files:
            raise HTTPError(404)

        self.render(
            os.path.join('simple', 'files.html'),
            package=pkg.lower_name,
            files=files
        )

    @classmethod
    @threaded
    @timeit
    def packages_list(cls, package):
        q = Package.select().join(
            PackageVersion
        ).join(
            PackageFile
        ).where(
            Package.lower_name == package.lower()
        ).limit(1)

        exists = q.count()
        is_proxy = q.where(Package.is_proxy == True).count()

        return exists, is_proxy, q[0] if exists else None

    @classmethod
    @timeit
    @coroutine
    def proxy_package(cls, package):
        try:
            remote_package_exists = yield PYPIClient.exists(package)

            if remote_package_exists:
                pkg_real_name = yield PYPIClient.find_real_name(package)
                pkg = yield proxy_remote_package(pkg_real_name)

                raise Return(pkg)

            raise LookupError("Remote package not found")
        except (LookupError, HTTPClientError) as e:
            if isinstance(e, HTTPClientError):
                log.warning("PYPI backend return an error: %s", e)

            raise Return(Package.find(package))
