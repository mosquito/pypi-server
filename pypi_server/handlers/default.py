#!/usr/bin/env python
# encoding: utf-8
from tornado import httputil
from .base import BaseHandler


class DefaultHandler(BaseHandler):
    def prepare(self):
        return self.send_error(404)