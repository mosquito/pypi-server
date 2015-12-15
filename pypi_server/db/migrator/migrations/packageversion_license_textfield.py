# encoding: utf-8
from playhouse.migrate import migrate
import peewee
from pypi_server.db.migrator import migration
from pypi_server.db.packages import PackageVersion


@migration(9)
def change_license_field_type(migrator, db):
    if isinstance(db, peewee.SqliteDatabase):
        # SQLite has not length
        return

    try:
        migrate(migrator.drop_column('packageversion', 'license_old'))
    except:
        pass

    with db.transaction():
        migrate(
            migrator.rename_column('packageversion', 'license', 'license_old'),
            migrator.add_column("packageversion", 'license', PackageVersion.license),
        )

        db.execute_sql("UPDATE packageversion SET license = license_old")
        migrate(migrator.drop_column('packageversion', 'license_old'))
