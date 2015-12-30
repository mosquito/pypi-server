# encoding: utf-8
import imp
import os
import re
import sys
import logging
from collections import namedtuple


log = logging.getLogger(__name__)
MIGRATION_EXP = re.compile(r"(?P<rev>\d+)_(?P<name>.*)\.py$")
Module = namedtuple("Module", ("name", "path", "rev"))

PATH = os.path.abspath(os.path.dirname(__file__))

MIGRATIONS = sorted(
    map(
        lambda x: Module(path=os.path.join(PATH, x.string), **x.groupdict()),
        filter(
            None,
            map(
                MIGRATION_EXP.match,
                os.listdir(PATH)
            )
        )
    ),
    key=lambda x: x.rev
)


for mod in MIGRATIONS:
    sys.modules["{}.{}".format(__name__, mod.name)] = imp.load_source(mod.name, mod.path)

