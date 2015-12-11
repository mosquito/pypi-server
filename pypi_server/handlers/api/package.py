# encoding: utf-8
from pypi_server.db.packages import Package, PackageVersion
from pypi_server.handlers import route
from pypi_server.handlers.api import JSONHandler
from pypi_server.handlers.api.login import authorization_required
from pypi_server.handlers.base import threaded
from pypi_server.handlers.pypi.proxy.client import normalize_package_name
from tornado.gen import coroutine
from tornado.web import HTTPError


@route('/api/v1/package/(?P<package>[\w\.\d\-\_]+)/?')
class PackageHandler(JSONHandler):
    @authorization_required()
    @coroutine
    def get(self, package):
        pkg = yield self.get_package(package)
        self.response((yield self.package_info(pkg)))

    @staticmethod
    @threaded
    def package_info(pkg):
        return {
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
        }

    @staticmethod
    @threaded
    def get_package(package):
        package = normalize_package_name(package)
        q = Package.select().join(PackageVersion).where(Package.lower_name == package).limit(1)

        if not q.count():
            raise HTTPError(404)

        return q[0]

    @authorization_required(is_admin=True)
    @coroutine
    def delete(self, package):
        pkg = yield self.get_package(package)
        yield self.thread_pool.submit(pkg.delete_instance, recursive=True)
        self.response({
            'package': pkg.lower_name,
            'deleted': True,
        })

    @authorization_required(is_admin=True)
    @coroutine
    def put(self, package):
        pkg = yield self.get_package(package)
        pkg.owner = self.json.get('owner', pkg.owner_id)

        if pkg.is_dirty():
            yield self.thread_pool.submit(pkg.save)

        self.response((yield self.package_info(pkg)))
