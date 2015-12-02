#!/usr/bin/env python
# encoding: utf-8
import logging

log = logging.getLogger("db.migrator")
MIGRATIONS = []


def migration(func):
    global MIGRATIONS

    MIGRATIONS.append((
        "{0.__module__}.{0.__name__}".format(func),
        func
    ))

    return func


import migrations
