# encoding: utf-8
from pypi_server.db.migrator import migration
from pypi_server.db.users import Users


@migration(2)
def create_default_user(migrator, db):
    Users(login='admin', password='admin', email="admin@example.net", is_admin=True).save()
