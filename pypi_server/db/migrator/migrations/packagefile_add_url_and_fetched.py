# encoding: utf-8
from playhouse.migrate import migrate
from pypi_server.db.migrator import migration
from pypi_server.db.packages import PackageFile


@migration(6)
def add_url_fileld(migrator, db):
    try:
        PackageFile.select(PackageFile.url).where(PackageFile.url == None).count()
    except:
        migrate(
            migrator.add_column(
                'packagefile',
                'url',
                PackageFile.url
            )
        )


@migration(7)
def add_fetched_fileld(migrator, db):
    try:
        PackageFile.select(PackageFile.fetched).where(PackageFile.fetched == None).count()
    except:
        migrate(
            migrator.add_column(
                'packagefile',
                'fetched',
                PackageFile.fetched
            )
        )
