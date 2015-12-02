#!/usr/bin/env python
# encoding: utf-8
import datetime
import peewee
from .. import Model


class Migrations(Model):
    name = peewee.CharField(max_length=255, null=False, index=True, unique=True)
    ts = peewee.DateTimeField(default=datetime.datetime.now, null=False)
