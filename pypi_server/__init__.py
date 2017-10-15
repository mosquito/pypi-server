# encoding: utf-8
import os
import sys

PY2 = (sys.version_info < (3,))


author_info = [
    ("Dmitry Orlov", "me@mosquito.su")
]

version_info = (0, 4, 4)

__version__ = ".".join(map(str, version_info))
__author__ = ", ".join("{0} <{1}>".format(*author) for author in author_info)

ROOT = os.path.abspath(os.path.dirname(__file__))
