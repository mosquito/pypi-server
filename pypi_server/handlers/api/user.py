# encoding: utf-8
from six import text_type
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
        except DoesNotExist:
            raise HTTPError(404)

        try:
            user.login = self.json.get("login", user.login)
            user.email = self.json.get("email", user.email)
            user.is_admin = bool(self.json.get("is_admin", user.is_admin))

            password = self.json.get("password")
            if password:
                user.password = password

            disabled = self.json.get("disabled")
            if disabled is False:
                user.disabled = False

            if not all((
                isinstance(user.login, text_type),
                isinstance(user.email, text_type),
                LOGIN_EXP.match(str(user.login)) is not None,
                user.password and len(user.password) > 3,
                EMAIL_EXP.match(str(user.email)) is not None,
            )):
                raise HTTPError(400)
        except:
            raise HTTPError(400)

        user.save()

        self.response({
            'id': user.id,
            'login': user.login,
            'email': user.email,
            'disabled': user.disabled,
            'is_admin': user.is_admin,
        })

    @authorization_required(is_admin=True)
    @threaded
    def delete(self, uid):
        try:
            user = Users.get(id=uid)
            user.disabled = True
        except (KeyError, AssertionError):
            raise HTTPError(400)
        except DoesNotExist:
            raise HTTPError(404)
        else:
            user.save()

        self.set_status(204)
