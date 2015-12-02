# encoding: utf-8
from .. import migration
from ...users import Users


@migration
def create_default_user(migrator, db):
    Users(login='admin', password='admin', email="admin@example.net", is_admin=True).save()
