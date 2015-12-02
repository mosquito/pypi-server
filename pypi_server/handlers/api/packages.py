# encoding: utf-8
import peewee
from collections import defaultdict
from peewee import DoesNotExist
from pypi_server.cache import Cache
from pypi_server.db.packages import Package, PackageVersion, PackageFile
from pypi_server.db.users import Users
from pypi_server.handlers import route
from pypi_server.handlers.base import threaded
from .login import authorization_required
from . import JSONHandler


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