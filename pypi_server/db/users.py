#!/usr/bin/env python
# encoding: utf-8
import peewee as p
from six import binary_type, text_type
from playhouse.fields import gensalt, hashpw
from pypi_server.db import Model
from tornado.log import app_log as log


def b(value):
    if isinstance(value, text_type):
        return value.encode('utf-8')

    if isinstance(value, binary_type):
        return value

    raise TypeError("Can't convert %r to binary explicit." % type(value))


def u(value):
    if isinstance(value, binary_type):
        return value.decode('utf-8')

    elif isinstance(value, text_type):
        return value

    raise TypeError("Can't convert %r to unicode explicit." % type(value))


class PasswordHash(text_type):
    __slots__ = ()

    def check_password(self, password):
        password = b(password)
        pw_hash = b(self)

        log.debug("Password: %r %r", self, password)
        return hashpw(password, pw_hash) == pw_hash


class PasswordField(p.TextField):
    __slots__ = ('bcrypt_iterations', )

    def __init__(self, iterations=12, *args, **kwargs):
        self.bcrypt_iterations = int(iterations)
        super(PasswordField, self).__init__(*args, **kwargs)

    def db_value(self, value):
        return value if value is None else u(
            hashpw(
                b(value),
                gensalt(self.bcrypt_iterations)
            )
        )

    def python_value(self, value):
        return PasswordHash(u(value))


class Users(Model):
    login = p.CharField(max_length=255, unique=True, index=True, null=False)
    password = PasswordField(iterations=10, null=False)
    disabled = p.BooleanField(default=False, null=False)
    is_admin = p.BooleanField(default=False, null=False)
    email = p.CharField(index=True)

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
