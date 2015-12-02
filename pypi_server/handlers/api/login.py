# encoding: utf-8
from functools import wraps
from pypi_server.cache import Cache
from pypi_server.db.users import Users
from pypi_server.handlers import route
from tornado.gen import Return, coroutine, maybe_future
from tornado.ioloop import IOLoop
from tornado.web import HTTPError
from peewee import DoesNotExist
from . import JSONHandler, threaded


SESSION_DAYS = 3
SESSION_SECS = SESSION_DAYS * 86400


@threaded
@Cache(60)
def find_user(uid, is_admin=False):
    cond = (
        Users.disabled == False,
        Users.id == uid,
    )
    if is_admin:
        cond += (Users.is_admin == is_admin,)

    q = Users.select().where(*cond)

    if not q.count():
        raise DoesNotExist("User doesn't exists")

    return q.limit(1)[0]


def reject(self, reason):
    self.clear_all_cookies()
    self.set_status(403)
    raise Return(self.response({
        'error': reason
    }))


def authorization_required(is_admin=False):
    def decorator(func):
        @wraps(func)
        @coroutine
        def wrap(self, *args, **kwargs):
            io_loop = IOLoop.current()

            uid, remote_ip, start_time = self.get_secure_cookie('session', (None, None, None))
            if not all((uid, remote_ip, start_time)):
                raise Return(reject(self, 'Not authorized'))

            if not (start_time + SESSION_SECS) > io_loop.time():
                raise Return(reject(self, 'Session expired'))

            self.current_user = yield find_user(uid, is_admin=is_admin)

            if self.current_user.disabled:
                raise Return(reject(self, 'User disabled'))

            result = yield maybe_future(func(self, *args, **kwargs))
            raise Return(result)

        return wrap
    return decorator


@route("/api/v1/login")
class LoginHandler(JSONHandler):
    @authorization_required()
    def get(self):
        raise Return(self.response({
            'login': self.current_user.login,
            'is_admin': self.current_user.is_admin,
        }))

    @threaded
    def post(self):
        login, password = self.json['login'], self.json['password']

        try:
            user = Users.check(login, password)
        except DoesNotExist:
            raise HTTPError(403)

        self.set_secure_cookie(
            'session',
            (
                user.id,
                self.request.remote_ip,
                IOLoop.current().time()
            ),
            SESSION_DAYS
        )

        return self.response({
            'login': user.login,
            'is_admin': user.is_admin,
        })
