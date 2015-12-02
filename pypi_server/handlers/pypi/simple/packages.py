#!/usr/bin/env python
# encoding: utf-8
import os
from tornado.gen import coroutine, Return
from tornado_xmlrpc.handler import XMLRPCHandler
from ... import route, add_slash
from ...base import BaseHandler, threaded
from ...pypi.proxy.client import PYPIClient
from ....db.packages import Package, PackageVersion, PackageFile


@route(r'/simple/?')
@add_slash
class PackagesHandler(BaseHandler, XMLRPCHandler):
    @coroutine
    def get(self):
        self.render(
            os.path.join('simple', 'packages.html'),
            packages=(yield threaded(Package.select)())
        )

    @threaded
    def rpc_package_releases(self, package_name, show_hidden=False):
        package = Package.select().where(Package.name == package_name)
        return list(map(lambda x: str(x.name), package.versions()))

    @threaded
    def rpc_release_urls(self, package_name, version):
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

    @threaded
    def rpc_list_packages(self):
        return list(map(lambda x: x.name, Package.select()))

    @coroutine
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

    @threaded
    def _search(self, names, descriptions, operator):
        op_and = lambda x, y: x & y
        op_or = lambda x, y: x | y

        operator_func = ({'or': op_or, 'and': op_and}).get(operator.lower(), op_and)
        result = []

        packages = PackageVersion.select().join(Package).where(
            operator_func(
                Package.name in tuple(names),
                PackageVersion.description.contains(descriptions)
            )
        )

        for pkg in packages:
            pkg_dict = dict(
                name=pkg.package.name,
                version=str(pkg.version.name),
                summary=pkg.version.description,
                _pypi_ordering=1,
            )

            result.append(pkg_dict)

        return result
