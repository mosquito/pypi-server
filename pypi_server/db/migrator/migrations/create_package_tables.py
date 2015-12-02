# encoding: utf-8
from .. import migration
from ...packages import Package, PackageFile, PackageVersion


@migration
def create_package(migrator, db):
    db.create_tables([Package])

@migration
def create_package_version(migrator, db):
    db.create_tables([PackageVersion])

@migration
def create_package_file(migrator, db):
    db.create_tables([PackageFile])
