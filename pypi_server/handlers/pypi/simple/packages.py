# encoding: utf-8
import os
from pypi_server.cache import Cache
from tornado.gen import coroutine, Return
from tornado_xmlrpc.handler import XMLRPCHandler
from pypi_server.handlers import route, add_slash
from pypi_server.handlers.base import BaseHandler, threaded
from pypi_server.handlers.pypi.proxy.client import PYPIClient
from pypi_server.db.packages import Package, PackageVersion, PackageFile


@route(r'/simple/?')
@add_slash
class PackagesHandler(BaseHandler, XMLRPCHandler):
    @coroutine
    def get(self):
        self.render(
            os.path.join('simple', 'packages.html'),
            packages=(yield self.pkg_list())
        )

    @classmethod
    @threaded
    @Cache(5, files_cache=True, ignore_self=True)
    def pkg_list(cls):
        return list(Package.select().order_by(Package.lower_name))

    @classmethod
    @threaded
    @Cache(5)
    def rpc_package_releases(cls, package_name, show_hidden=False):
        package = Package.select().where(Package.name == package_name)
        return list(map(lambda x: str(x.name), package.versions()))

    @classmethod
    @threaded
    @Cache(5)
    def rpc_release_urls(cls, package_name, version):
        raise Return(
            list(
                map(
                    lambda x: "/".join((version, x.name)),
                    PackageFile.select().join(
                        Package
                    ).join(
                        PackageVersion
                    ).where(
                        Package.name == package_name,
                        PackageVersion.version == version
                    )
                )
            )
        )

    @classmethod
    @threaded
    @Cache(5)
    def rpc_list_packages(cls):
        return list(map(lambda x: x.name, Package.select()))

    @coroutine
    @Cache(60, files_cache=True)
    def rpc_search(self, query, operator='or'):
        results = []

        assert operator in ("and", "or"), "Operator must be 'and' or 'or'"

        names = tuple(query.get('name', []))
        descriptions = tuple(query.get('summary', []))

        async_queries = yield [
            self._search(names, descriptions, operator),
            PYPIClient.search(names, descriptions, operator)
        ]

        for res in async_queries:
            for result in res:
                results.append(result)

        raise Return(results)

    @classmethod
    @threaded
    @Cache(5)
    def _search(self, names, descriptions, operator):
        op_and = lambda x, y: x & y
        op_or = lambda x, y: x | y

        operator_func = ({'or': op_or, 'and': op_and}).get(operator.lower(), op_and)
        result = []

        packages = PackageVersion.select(
            Package.name,
            PackageVersion,
        ).join(Package).where(
            operator_func(
                Package.name in tuple(names),
                PackageVersion.description.contains(descriptions)
            )
        )

        for version in packages:
            pkg_dict = dict(
                name=version.package.name,
                version=str(version.version),
                summary=version.description,
                _pypi_ordering=1,
            )

            result.append(pkg_dict)

        return result
