# encoding: utf-8
import os
from pypi_server.timeit import timeit
from tornado.gen import coroutine, Return
from tornado.web import HTTPError
from pypi_server.handlers import route, add_slash
from pypi_server.handlers.base import BaseHandler, threaded
from pypi_server.handlers.pypi.proxy.client import PYPIClient
from pypi_server.db.packages import PackageVersion, Package, PackageFile


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


@coroutine
def proxy_remote_package(package):
    pkg = Package.get_or_create(name=package, proxy=True)

    releases, fetched_releases = yield [PYPIClient.releases(pkg.name), threaded(pkg.versions)()]
    fetched_releases = set(map(lambda x: x.version, fetched_releases))
    new_releases = releases - fetched_releases
    versions = yield [release_fetch(pkg, release) for release in new_releases]

    writers = []

    for version, files in versions:
        for remote_file in files:
            writers.append(
                write_file(version, remote_file['filename'], remote_file['file'].body)
            )

    yield writers

    raise Return(pkg)


@threaded
def write_file(version, filename, data):
    pkg_file = version.create_file(filename)
    with pkg_file.open('w+') as f:
        f.write(data)

    pkg_file.save()
    return pkg_file


@coroutine
def release_fetch(package, rel):
    version = package.create_version(rel)
    version_info, releases = yield [
        PYPIClient.release_data(package.name, rel),
        PYPIClient.release_files(package.name, rel)
    ]

    for key, val in PACKAGE_META.items():
        setattr(version, key, version_info.get(val if val else key))

    version.save()

    raise Return((version, releases))


@route(r'/simple/(?P<package>[\w\.\d\-\_]+)/?')
@add_slash
class VersionsHandler(BaseHandler):
    @timeit
    @coroutine
    def get(self, package):
        exists, is_proxy, pkg = yield self.packages_list(package)

        if not exists or is_proxy:
           pkg = yield self.proxy_package(package)

        if not pkg:
            raise HTTPError(404)

        files = yield threaded(pkg.files)()

        self.render(
            os.path.join('simple', 'files.html'),
            package=pkg.lower_name,
            files=files
        )

    @threaded
    @timeit
    def packages_list(self, package):
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

    @timeit
    @coroutine
    def proxy_package(self, package):
        if (yield PYPIClient.exists(package)):
            pkg_real_name = yield PYPIClient.find_real_name(package)
            pkg = yield proxy_remote_package(pkg_real_name)

            raise Return(pkg)

        raise LookupError("Remote package not found")
