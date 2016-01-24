#!/usr/bin/env python
# encoding: utf-8
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

    @gen_test
    def test_user_list(self):
        client = yield self.auth_client()

        response = yield client.fetch(self.get_url("/api/v1/users"), "GET")
        for user in response.body:
            self.assertIn('disabled', user)
            self.assertIn('email', user)
            self.assertIn('id', user)
            self.assertIn('is_admin', user)
            self.assertIn('login', user)

    @gen_test
    def test_create_user(self):
        client = yield self.auth_client()

        user = {
            "email": "vpupkin@gmail.com",
            "login": "vpupkin",
            "is_admin": True,
            "password": "secretPassw0rd",
        }

        response = yield client.fetch(self.get_url("/api/v1/users"), "POST", user)

        self.assertIn('id', response.body)

    @gen_test
    def test_create_user_conflict(self):
        client = yield self.auth_client()

        user = {
            "email": "vpupkin@gmail.com",
            "login": "admin",
            "is_admin": True,
            "password": "secretPassw0rd",
        }

        with self.assertRaises(HTTPError) as err:
            yield client.fetch(self.get_url("/api/v1/users"), "POST", user)

        self.assertEqual(err.exception.code, 409)

    @gen_test
    def test_create_user_invalid(self):
        client = yield self.auth_client()

        user = {
            "email": True,
            "login": True,
            "is_admin": True,
            "password": True,
        }

        with self.assertRaises(HTTPError) as err:
            yield client.fetch(self.get_url("/api/v1/users"), "POST", user)

        self.assertEqual(err.exception.code, 400)
