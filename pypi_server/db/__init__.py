#!/usr/bin/env python
# encoding: utf-8
import logging
import os
import peewee
from slimurl import URL
from peewee import Proxy, SqliteDatabase, MySQLDatabase, PostgresqlDatabase
from playhouse.migrate import SqliteMigrator, MySQLMigrator, PostgresqlMigrator

DB = Proxy()


class Model(peewee.Model):
    class Meta:
        database = DB


from .migrator.model import Migrations
from pypi_server.db.migrator.actions import migrate_db

log = logging.getLogger('db')


def init_sqlite(url):
    global DB
    dbfile = os.path.join("/", *url.path.split("/"))
    dirname = os.path.dirname(dbfile)

    log.info('Opening sqlite database: %s', dbfile)

    if not os.path.exists(dirname):
        os.makedirs(dirname)

    DB.initialize(SqliteDatabase(dbfile))
    return DB, SqliteMigrator(DB)


def init_mysql(url):
    global DB

    DB.initialize(MySQLDatabase(
        database=url.path.strip("/"),
        user=url.user or '',
        password=url.password or '',
        host=url.host,
        autocommit=bool(url.get('autocommit', '')),
        autorollback=bool(url.get('autorollback', ''))
    ))

    return DB, MySQLMigrator(DB)


def init_postgres(url):
    global DB
    DB.initialize(PostgresqlDatabase(
        database=url.path.strip("/"),
        user=url.user or '',
        password=url.password or '',
        host=url.host,
        autocommit=bool(url.get('autocommit', '')),
        autorollback=bool(url.get('autorollback', ''))
    ))

    return DB, PostgresqlMigrator


DB_ENGINES = {
    'sqlite': init_sqlite,
    'sqlite3': init_sqlite,
    'mysql': init_mysql,
    'postgresql': init_postgres,
    'postgres': init_postgres,
    'pg': init_postgres,
}


def init_db(db_url):
    global DB
    db_url = URL(db_url)
    DB, migrator = DB_ENGINES.get(
        db_url.scheme,
        lambda x: log.fatal("Unable to fund database driver")
    )(db_url)

    path = os.path.abspath(db_url.path)
    db_dir = os.path.dirname(path)

    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    DB.create_tables([Migrations], safe=True)

    log.info("Database initialized as '%s'. Checking migrations...", path)
    migrate_db(DB, Migrations, migrator)
