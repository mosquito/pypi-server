# encoding: utf-8
import os
from tornado.gen import coroutine, Return
from tornado.web import HTTPError
from ... import route, add_slash
from ...base import BaseHandler, threaded
from ...pypi.proxy.client import PYPIClient
from ....db.packages import PackageVersion, Package, PackageFile


@route(r'/simple/(?P<package>[\w\.\d\-\_]+)/?')
@add_slash
class VersionsHandler(BaseHandler):
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
    def get(self, package):
        files = yield self.files(package)

        files = list(files or [])

        pkg_real_name = package

        if not files:
            if (yield PYPIClient.exists(package)):
                pkg_real_name = yield PYPIClient.find_real_name(package)
                files = yield self.proxy_remote_package(pkg_real_name)

        if not files:
            raise HTTPError(404)

        self.render(
            os.path.join('simple', 'files.html'),
            package=pkg_real_name,
            files=files
        )

    @classmethod
    @coroutine
    def proxy_remote_package(cls, package):
        pkg = Package.get_or_create(name=package, proxy=True)

        releases = yield PYPIClient.releases(pkg.name)
        versions = yield [cls.release_fetch(pkg, release) for release in releases]

        writers = []

        for version, files in versions:
            for remote_file in files:
                writers.append(
                    cls.write_file(version, remote_file['filename'], remote_file['file'].body)
                )

        result_files = yield writers
        raise Return(result_files)

    @classmethod
    @threaded
    def write_file(cls, version, filename, data):
        pkg_file = version.create_file(filename)
        with pkg_file.open('w+') as f:
            f.write(data)

        pkg_file.save()
        return pkg_file

    @classmethod
    @coroutine
    def release_fetch(cls, package, rel):
        version = package.create_version(rel)
        version_info, releases = yield [
            PYPIClient.release_data(package.name, rel),
            PYPIClient.release_files(package.name, rel)
        ]

        for key, val in cls.PACKAGE_META.items():
            setattr(version, key, version_info.get(val if val else key))

        version.save()

        raise Return((version, releases))

    @threaded
    def files(self, name):
        files = PackageFile.select(
        ).join(
            PackageVersion
        ).join(
            Package
        ).where(
            Package.name == name,
            PackageVersion.hidden == False,
        ).order_by(
            Package.name.asc(),
            PackageVersion.version.desc()
        )

        if not files.count():
            return []

        return files
