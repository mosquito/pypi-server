# encoding: utf-8
from peewee import OperationalError, ProgrammingError, PostgresqlDatabase
from playhouse.migrate import migrate
from pypi_server.db.migrator import migration


@migration(8)
def add_uniquie_basename_index(migrator, db):
    if isinstance(db.obj, PostgresqlDatabase):
        # Index already exists from previous migrations
        return
    try:
        migrate(
            migrator.add_index('packagefile', ('basename',), True)
        )
    except (OperationalError, ProgrammingError):
        pass
