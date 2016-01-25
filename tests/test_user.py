# encoding: utf-8
import uuid
import itertools
from tornado.log import app_log as log

from . import *


class TestAPILogin(TestCase):
    USER = {
        "login": "admin",
        "password": "admin",
    }

    @coroutine
    def auth_client(self):
        client = self.get_rest_client()
        yield client.fetch(self.get_url("/api/v1/login"), "POST", self.USER)

        raise Return(client)

    @coroutine
    def create_user(self, clinet):
        client = yield self.auth_client()

        user = {
            "email": "vpupkin@gmail.com",
            "login": "vpupkin",
            "is_admin": True,
            "password": "secretPassw0rd",
        }

        response = yield client.fetch(self.get_url("/api/v1/users"), "POST", user)
        raise Return(response.body)

    @gen_test
    def test_get_user(self):
        client = yield self.auth_client()
        user = yield self.create_user(client)

        response = yield client.fetch(
            self.get_url("/api/v1/user/{0}".format(user['id'])),
            "GET"
        )

        self.assertEqual(user['id'], response.body['id'])
        for key in ("disabled", "email", "id", "is_admin", "login", "packages"):
            self.assertIn(key, response.body)

    @gen_test
    def test_put_user(self):
        client = yield self.auth_client()
        user = yield self.create_user(client)

        cases = [
            ("login", "foofoofoo"),
            ("email", "aaa@bbb.com"),
            ("is_admin", False),
            ("password", str(uuid.uuid4()))
        ]

        for i in range(1, len(cases)):
            for case in itertools.combinations(cases, i):
                body = dict(case)
                log.info("Send body: %r", body)
                response = yield client.fetch(
                    self.get_url("/api/v1/user/{0}".format(user['id'])),
                    "PUT", body
                )

                for k, v in body.items():
                    if k == 'password':
                        continue

                    self.assertIn(k, response.body)
                    self.assertEqual(v, response.body[k])

    @gen_test
    def test_delete_user(self):
        client = yield self.auth_client()
        user = yield self.create_user(client)

        response = yield client.fetch(
            self.get_url("/api/v1/user/{0}".format(user['id'])), 'DELETE'
        )

        self.assertEqual(response.code, 204)

    @gen_test
    def test_get_user(self):
        client = yield self.auth_client()

        with self.assertRaises(HTTPError) as err:
            yield client.fetch(
                self.get_url("/api/v1/user/0"),
                "GET"
            )

        self.assertEqual(err.exception.code, 404)

    @gen_test(timeout=99999999999)
    def test_put_errors(self):
        client = yield self.auth_client()
        user = yield self.create_user(client)

        cases = [
            ("login", False),
            ("login", [2, 3]),
            ("email", "@bbb.com"),
            ("email", {1: 2}),
            ("password", "123"),
            ("password", "1"),
            ("password", False),
            ("password", [1, '2']),
            ("password", {1: '2'}),
        ]

        for i in range(1, len(cases)):
            for case in itertools.combinations(cases, i):
                body = dict(case)

                with self.assertRaises(HTTPError) as err:
                    log.info("Body: %s", body)
                    yield client.fetch(
                        self.get_url("/api/v1/user/{0}".format(user['id'])),
                        "PUT", body
                    )

                self.assertEqual(err.exception.code, 400)
