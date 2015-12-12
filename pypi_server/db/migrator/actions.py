# encoding: utf-8
from pypi_server.db.migrator import MIGRATIONS, log


def migrate_db(DB, Migrations, migrator):
    migrations = sorted(MIGRATIONS, key=lambda x: x[0])

    q = Migrations.select(Migrations.id).order_by(Migrations.id.desc())

    if q.count():
        last_applied_migration = q[0].id
    else:
        last_applied_migration = -1

    for migration_id, name, migration in filter(lambda x: x[0] > last_applied_migration, migrations):
        tran = DB.transaction()

        try:
            log.info('Applying migration: "%s"', name)
            migration(migrator, DB)
            Migrations.create(
                id=migration_id,
                name=name
            )
        except Exception as e:
            log.error("Migration failed.")
            log.exception(e)
            tran.rollback()
            raise
        else:
            tran.commit()
