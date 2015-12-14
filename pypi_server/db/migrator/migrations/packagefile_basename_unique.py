# encoding: utf-8
from peewee import OperationalError, ProgrammingError
from playhouse.migrate import migrate
from pypi_server.db.migrator import migration


@migration(8)
def add_uniquie_basename_index(migrator, db):
    try:
        migrate(
            migrator.add_index('packagefile', ('basename',), True)
        )
    except (OperationalError, ProgrammingError):
        pass
