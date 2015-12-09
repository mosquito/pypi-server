# encoding: utf-8
from pypi_server.db.packages import Package, PackageVersion, PackageFile
from pypi_server.handlers import route
from pypi_server.handlers.base import threaded
from pypi_server.handlers.pypi.proxy.client import normalize_package_name
from tornado.web import HTTPError
from pypi_server.handlers.api.login import authorization_required
from pypi_server.handlers.api import JSONHandler


@route('/api/v1/package/(?P<package>[\w\.\d\-\_]+)/?')
class PackageHandler(JSONHandler):
    @authorization_required()
    @threaded
    def get(self, package):
        package = normalize_package_name(package)
        q = Package.select().join(PackageVersion).where(Package.lower_name == package).limit(1)

        if not q.count():
            raise HTTPError(404)

        pkg = q[0]

        self.response({
            'name': pkg.lower_name,
            'owner': pkg.owner_id,
            'proxy': pkg.is_proxy,
            'versions': list(
                map(
                    str,
                    sorted(
                        map(
                            lambda x: x.version,
                            pkg.packageversion_set
                        ),
                        reverse=True
                    )
                )
            )
        })


@route('/api/v1/package/(?P<package>[\w\.\d\-\_]+)/(?P<version>[\w\d\.]+)/?')
class PackageVersionHandler(JSONHandler):
    @authorization_required()
    @threaded
    def get(self, package, version):
        package = normalize_package_name(package)
        q = PackageVersion.select().join(Package).join(PackageFile).where(
            Package.lower_name == package,
            PackageVersion.version == version,
        ).limit(1)

        if not q.count():
            raise HTTPError(404)

        ver = q[0]

        self.response({
           'version': str(ver.version),
            "hidden": ver.hidden,
            "downloads": ver.downloads,
            "author": ver.author,
            "author_email": ver.author_email,
            "maintainer": ver.maintainer,
            "maintainer_email": ver.maintainer_email,
            "home_page": ver.home_page,
            "license": ver.license,
            "summary": ver.summary,
            "description": ver.description,
            "keywords": ver.keywords,
            "platform": ver.platform,
            "download_url": ver.download_url,
            "classifiers": ver.classifiers,
            "requires": ver.requires,
            "requires_dist": ver.requires_dist,
            "provides": ver.provides,
            "provides_dist": ver.provides_dist,
            "requires_external": ver.requires_external,
            "requires_python": ver.requires_python,
            "obsoletes": ver.obsoletes,
            "obsoletes_dist": ver.obsoletes_dist,
            "project_url": ver.project_url,
            "files": list(map(
                lambda f: dict(
                    name=f.basename,
                    url="/package/{0}/{1}/{2}".format(ver.package.lower_name, ver.version, f.basename)
                ),
                ver.packagefile_set
            ))
        })
