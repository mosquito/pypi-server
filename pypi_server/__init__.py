# encoding: utf-8
import os
import sys

PY2 = (sys.version_info < (3,))

try:
    __import__('__pypy__')
    IS_PYPY = True
except ImportError:
    IS_PYPY = False

author_info = [
    ("Dmitry Orlov", "me@mosquito.su")
]

version_info = (0, 1, 11)

__version__ = ".".join(map(str, version_info))
__author__ = ", ".join("{0} <{1}>".format(*author) for author in author_info)

ROOT = os.path.abspath(os.path.dirname(__file__))
