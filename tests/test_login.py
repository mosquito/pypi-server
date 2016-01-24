#!/usr/bin/env python
# encoding: utf-8
from . import *


class TestAPILogin(TestCase):
    USER = {
        "login": "admin",
        "password": "admin",
    }

    @coroutine
    def get_auth(self, client):
        response = yield client.fetch(self.get_url("/api/v1/login"), "GET")
        raise Return(response)

    @coroutine
    def post_auth(self, client):
        response = yield client.fetch(self.get_url("/api/v1/login"), "POST", self.USER)

        raise Return(response)

    @gen_test
    def test_get_no_auth(self):
        client = self.get_rest_client()

        with self.assertRaises(HTTPError) as err:
            yield self.get_auth(client)

        self.assertEqual(err.exception.code,  403)

    @gen_test
    def test_post_auth(self):
        client = self.get_rest_client()
        response = yield self.post_auth(client)

        self.assertEqual(response.body['login'], self.USER['login'])
        self.assertEqual(response.body['is_admin'], True)

    @gen_test
    def test_get_and_post_auth(self):
        client = self.get_rest_client()
        response = yield self.post_auth(client)

        self.assertEqual(response.body['login'], self.USER['login'])
        self.assertEqual(response.body['is_admin'], True)

        response = yield self.get_auth(client)
        self.assertEqual(response.body['login'], self.USER['login'])
        self.assertEqual(response.body['is_admin'], True)
