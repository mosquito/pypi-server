# encoding: utf-8
from peewee import DoesNotExist
from tornado.web import HTTPError
from pypi_server.db.users import Users
from pypi_server.handlers import route
from pypi_server.handlers.base import threaded
from pypi_server.handlers.api import JSONHandler
from pypi_server.handlers.api.login import authorization_required
from pypi_server.handlers.api.users import LOGIN_EXP, EMAIL_EXP


@route('/api/v1/user/(\d+)/?')
class UserHandler(JSONHandler):
    @authorization_required(is_admin=True)
    @threaded
    def get(self, uid):
        try:
            user = Users.get(id=uid)
        except DoesNotExist:
            raise HTTPError(404)

        self.response(dict(
            id=user.id,
            login=user.login,
            email=user.email,
            is_admin=user.is_admin,
            disabled=user.disabled,
            packages=list(
                map(
                    lambda x: x.name,
                    user.package_set
                )
            )
        ))

    @authorization_required(is_admin=True)
    @threaded
    def put(self, uid):
        try:
            user = Users.get(id=uid)
            user.login = self.json["login"]
            user.email = self.json["email"]
            user.is_admin = bool(self.json.get("is_admin", 0))
            user.password = self.json["password"]

            assert user.password and len(user.password) > 3
            assert LOGIN_EXP.match(user.login)
            assert EMAIL_EXP.match(user.email)
        except (KeyError, AssertionError):
            raise HTTPError(400)
        except DoesNotExist:
            raise HTTPError(404)
        else:
            user.save()

            self.response({
                'id': user.id,
                'login': user.login,
                'email': user.email,
                'is_admin': user.is_admin,
            })