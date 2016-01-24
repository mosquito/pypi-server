# encoding: utf-8
import re
from tornado.web import HTTPError
from pypi_server.db.users import Users
from pypi_server.handlers import route
from pypi_server.handlers.base import threaded
from pypi_server.handlers.api import JSONHandler
from pypi_server.handlers.api.login import authorization_required


LOGIN_EXP = re.compile("^[\d\w\.\-\@\_]+$")
EMAIL_EXP = re.compile("^[^\@]+\@\S+$")


@route('/api/v1/users/?')
class UsersHandler(JSONHandler):
    @authorization_required(is_admin=True)
    @threaded
    def get(self):
        self.response(
            list(
                map(
                    lambda x: dict(
                        id=x.id,
                        login=x.login,
                        email=x.email,
                        is_admin=x.is_admin,
                        disabled=x.disabled,
                    ),
                    Users.select(
                        Users.id,
                        Users.login,
                        Users.email,
                        Users.is_admin,
                        Users.disabled
                    )
                )
            )
        )

    @authorization_required(is_admin=True)
    @threaded
    def post(self):
        try:
            login = self.json["login"]
            email = self.json["email"]
            is_admin = bool(self.json.get("is_admin", 0))
            password = self.json["password"]

            assert password and len(password) > 3
            assert LOGIN_EXP.match(login)
            assert EMAIL_EXP.match(email)
        except (KeyError, AssertionError, TypeError):
            raise HTTPError(400)

        if Users.select().where(Users.login == login).count():
            raise HTTPError(409)

        user = Users(
            login=login,
            email=email,
            is_admin=is_admin,
            password=password,
        )

        user.save()

        self.response({
            'id': user.id,
            'login': user.login,
            'email': user.email,
            'is_admin': user.is_admin,
        })
