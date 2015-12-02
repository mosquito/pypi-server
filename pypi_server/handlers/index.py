#!/usr/bin/env python
# encoding: utf-8
import os
from tornado.gen import coroutine
from . import route
from .base import BaseHandler, threaded
from ..http_cache import HTTPCache
from ..cache import Cache


@route(r"^/$")
class IndexHander(BaseHandler):
    @HTTPCache(600, True, 60)
    @coroutine
    @Cache(60, ignore_self=True)
    def get(self):
        base_dir = self.application.settings['base_dir']
        vendor, application, styles = yield [
            self.find(base_dir, 'static/vendor', '.js'),
            self.find(base_dir, 'static/js', '.js'),
            self.find(base_dir, 'static', 'style.css'),
        ]

        self.render(
            'index.html',
            vendor=vendor,
            application=application,
            styles=styles,
        )

    @staticmethod
    @threaded
    @Cache(60)
    def find(base_dir, path, pattern):
        file_list = []

        for root, dirs, files in os.walk(os.path.join(base_dir, *path.split('/'))):
            for f in filter(lambda x: x.endswith(pattern), files):
                rel_file = "/".join(os.path.split(os.path.join(root, f))).replace("/".join(os.path.split(base_dir)), '/')
                file_list.append("/{}".format(rel_file.strip("/")))

        return file_list