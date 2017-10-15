# encoding: utf-8
import peewee
from pypi_server.db.packages import Package
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
            Package.name,
            Users.login,
        ).join(
            Users, peewee.JOIN.LEFT_OUTER
        ).order_by(
            Package.is_proxy.asc(),
            Package.lower_name.asc(),
        )

        self.response(
            list(
                map(
                    lambda x: dict(
                        name=x.name,
                        owner={
                            'id': x.owner_id,
                            'name': x.owner.login if x.owner else None
                        },
                        is_proxy=x.is_proxy,
                    ),
                    q
                )
            )
        )
