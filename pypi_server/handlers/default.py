#!/usr/bin/env python
# encoding: utf-8
from pypi_server.handlers.base import BaseHandler


class DefaultHandler(BaseHandler):
    def prepare(self):
        return self.send_error(404)
