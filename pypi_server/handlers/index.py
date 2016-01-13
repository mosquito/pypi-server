#!/usr/bin/env python
# encoding: utf-8
import os
from tornado.gen import coroutine
from pypi_server.handlers import route
from pypi_server.handlers.base import BaseHandler, threaded
from pypi_server.http_cache import HTTPCache
from pypi_server.cache import Cache
from pypi_server import ROOT


@route(r"^/$")
class IndexHander(BaseHandler):
    @HTTPCache(600, True, 60)
    @coroutine
    def get(self):
        vendor_js, vendor_css, application, styles = yield [
            self.find(ROOT, 'static/vendor', '.js'),
            self.find(ROOT, 'static/vendor', '.css'),
            self.find(ROOT, 'static/js', '.js'),
            self.find(ROOT, 'static', 'style.css'),
        ]

        self.render(
            'index.html',
            vendor_js=vendor_js,
            vendor_css=vendor_css,
            application=application,
            styles=styles,
        )

    @staticmethod
    @threaded
    @Cache(5)
    def find(base_dir, path, pattern):
        file_list = []

        for root, dirs, files in os.walk(os.path.join(base_dir, *path.split('/'))):
            for f in filter(lambda x: x.endswith(pattern), files):
                rel_file = "/".join(os.path.split(os.path.join(root, f))).replace("/".join(os.path.split(base_dir)), '/')
                file_list.append("/{}".format(rel_file.strip("/")))

        return file_list