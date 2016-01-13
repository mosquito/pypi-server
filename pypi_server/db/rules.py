# encoding: utf-8
import peewee as p
from pypi_server.db import Model
from pypi_server.db.users import Users
from playhouse.fields import ManyToManyField


class Groups(Model):
    name = p.CharField(max_length=255, unique=True, index=True, null=False)
    disabled = p.BooleanField(default=False, null=False)

    @classmethod
    def check(cls, login, password):
        q = cls.select(cls.id, cls.password).where(
            cls.disabled == False,
            cls.login == str(login),
        )

        user = q.limit(1)
        user = user[0] if user else None

        if user and user.password.check_password(password):
            return cls.get(id=user.id)
        else:
            raise p.DoesNotExist("User doesn't exists")


class Participant(Model):
    user = p.ForeignKeyField(Users, unique=False, index=True)
    group = p.ForeignKeyField(Groups, unique=False, index=True)
    rules = ManyToManyField()
