# encoding: utf-8
import logging

log = logging.getLogger("db.migrator")
MIGRATIONS = []


def migration(version):
    def decorator(func):
        global MIGRATIONS

        MIGRATIONS.append((
            version,
            "{0.__module__}.{0.__name__}".format(func),
            func
        ))

        return func
    return decorator


import pypi_server.db.migrator.migrations
