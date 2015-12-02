# encoding: utf-8
from .. import migration
from ...users import Users


@migration
def create_users(migrator, db):
    db.create_tables([Users])
