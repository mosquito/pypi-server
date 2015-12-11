# encoding: utf-8
from pypi_server.db.migrator import migration
from pypi_server.db.users import Users


@migration(1)
def create_users(migrator, db):
    db.create_tables([Users])
