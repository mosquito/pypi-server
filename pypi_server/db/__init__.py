# encoding: utf-8
import logging
import os
from playhouse.signals import Model as SignalsModel
from slimurl import URL
from peewee import Proxy, SqliteDatabase, MySQLDatabase, PostgresqlDatabase
from playhouse.migrate import SqliteMigrator, MySQLMigrator, PostgresqlMigrator

DB = Proxy()


class Model(SignalsModel):
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
    log.info("Database initialized as '%s'. Checking migrations...", dbfile)
    return DB, SqliteMigrator(DB)


def init_mysql(url):
    global DB

    db_name = url.path.strip("/")

    DB.initialize(MySQLDatabase(
        database=db_name,
        user=url.user or '',
        password=url.password or '',
        host=url.host,
        autocommit=bool(url.get('autocommit', True)),
        autorollback=bool(url.get('autorollback', True))
    ))
    log.info("Database initialized as '%s'. Checking migrations...", db_name)
    return DB, MySQLMigrator(DB)


def init_postgres(url):
    global DB

    db_name = url.path.strip("/")

    DB.initialize(PostgresqlDatabase(
        database=db_name,
        user=url.user or '',
        password=url.password or '',
        host=url.host,
        autocommit=bool(url.get('autocommit', True)),
        autorollback=bool(url.get('autorollback', True))
    ))
    log.info("Database initialized as '%s'. Checking migrations...", db_name)
    return DB, PostgresqlMigrator(DB)


DB_ENGINES = {
    'sqlite': init_sqlite,
    'sqlite3': init_sqlite,
    'mysql': init_mysql,
    'postgresql': init_postgres,
    'postgres': init_postgres,
    'pg': init_postgres,
}


def init_db(db_url):
    db_url = URL(db_url)
    DB, migrator = DB_ENGINES.get(
        db_url.scheme,
        lambda x: log.fatal("Unable to fund database driver")
    )(db_url)

    DB.create_tables([Migrations], safe=True)
    migrate_db(DB, Migrations, migrator)
