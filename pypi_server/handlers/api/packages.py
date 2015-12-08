# encoding: utf-8
from pypi_server.db.packages import Package, PackageVersion, PackageFile
from pypi_server.handlers import route
from pypi_server.handlers.api import JSONHandler
from pypi_server.handlers.base import threaded
from pypi_server.handlers.api.login import authorization_required


@route('/api/v1/packages/?')
class PackagesHandler(JSONHandler):
    @authorization_required()
    @threaded
    def get(self):
        q = Package.select().join(PackageVersion)

        self.response(
            list(
                map(
                    lambda x: dict(
                        name=x.name,
                        owner=x.owner_id
                    ),
                    q
                )
            )
        )