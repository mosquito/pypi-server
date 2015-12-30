# encoding: utf-8
from pypi_server.db.migrator import migration
from pypi_server.db.packages import Package, PackageFile, PackageVersion


@migration(3)
def create_package(migrator, db):
    db.create_tables([Package])


@migration(4)
def create_package_version(migrator, db):
    db.create_tables([PackageVersion])


@migration(5)
def create_package_file(migrator, db):
    db.create_tables([PackageFile])
