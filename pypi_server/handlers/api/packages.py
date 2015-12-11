# encoding: utf-8
import peewee
from pypi_server.db.packages import Package, PackageVersion, PackageFile
from pypi_server.db.users import Users
from pypi_server.handlers import route
from pypi_server.handlers.api import JSONHandler
from pypi_server.handlers.base import threaded
from pypi_server.handlers.api.login import authorization_required


@route('/api/v1/packages/?')
class PackagesHandler(JSONHandler):
    @authorization_required()
    @threaded
    def get(self):
        q = Package.select(
            Package,
            Users.login,
        ).join(
            Users, peewee.JOIN.LEFT_OUTER
        )

        self.response(
            list(
                map(
                    lambda x: dict(
                        name=x.name,
                        owner={
                            'id': x.owner_id,
                            'name': x.owner.login
                        },
                        is_proxy=x.is_proxy,
                    ),
                    q
                )
            )
        )