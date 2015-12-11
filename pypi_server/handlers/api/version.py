#!/usr/bin/env python
# encoding: utf-8
from tornado.gen import coroutine
from tornado.web import HTTPError
from pypi_server.db.packages import PackageVersion, Package, PackageFile
from pypi_server.handlers import route
from pypi_server.handlers.api import JSONHandler
from pypi_server.handlers.api.login import authorization_required
from pypi_server.handlers.base import threaded
from pypi_server.handlers.pypi.proxy.client import normalize_package_name


@route('/api/v1/package/(?P<package>[\w\.\d\-\_]+)/(?P<version>[\w\d\.]+)/?')
class PackageVersionHandler(JSONHandler):
    @authorization_required()
    @coroutine
    def get(self, package, version):
        ver = yield self.get_version(package, version)
        self.response((yield self.version_info(ver)))

    @coroutine
    def put(self, package, version):
        ver = yield self.get_version(package, version)
        ver.hidden = self.json.get('hidden', version.hidden)

        if ver.is_dirty:
            yield self.thread_pool.submit(ver.save)

        self.response((yield self.version_info(ver)))

    @authorization_required(is_admin=True)
    @coroutine
    def delete(self, package, version):
        ver = yield self.get_version(package, version)
        yield self.thread_pool.submit(ver.delete_instance, recursive=True)

    @staticmethod
    @threaded
    def get_version(package, version):
        package = normalize_package_name(package)
        q = PackageVersion.select().join(Package).join(PackageFile).where(
            Package.lower_name == package,
            PackageVersion.version == version,
        ).limit(1)

        if not q.count():
            raise HTTPError(404)

        return q[0]

    @staticmethod
    @threaded
    def version_info(version):
        return {
            "version": str(version.version),
            "hidden": version.hidden,
            "downloads": version.downloads,
            "author": version.author,
            "author_email": version.author_email,
            "maintainer": version.maintainer,
            "maintainer_email": version.maintainer_email,
            "home_page": version.home_page,
            "license": version.license,
            "summary": version.summary,
            "description": version.description,
            "keywords": version.keywords,
            "platform": version.platform,
            "download_url": version.download_url,
            "classifiers": version.classifiers,
            "requires": version.requires,
            "requires_dist": version.requires_dist,
            "provides": version.provides,
            "provides_dist": version.provides_dist,
            "requires_external": version.requires_external,
            "requires_python": version.requires_python,
            "obsoletes": version.obsoletes,
            "obsoletes_dist": version.obsoletes_dist,
            "project_url": version.project_url,
            "files": list(map(
                lambda f: dict(
                    name=f.basename,
                    url="/package/{0}/{1}/{2}".format(version.package.lower_name, version.version, f.basename)
                ),
                version.packagefile_set
            ))
        }
