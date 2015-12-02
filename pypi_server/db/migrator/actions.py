#!/usr/bin/env python
# encoding: utf-8
from . import MIGRATIONS, log


def migrate_db(DB, Migrations, migrator):
    migration_history = dict(map(lambda x: (x.name, x.ts), Migrations.select()))

    for name, migration in MIGRATIONS:
        if name not in migration_history:
            try:
                with DB.transaction():
                    log.info('Applying migration: "%s"', name)
                    migration(migrator, DB)
            except Exception as e:
                log.error("Migration failed.")
                log.exception(e)
                DB.rollback()
                raise
            else:
                Migrations(name=name).save()
                DB.commit()
        else:
            log.debug('Migration "%s" already applied on %s', name, migration_history[name])