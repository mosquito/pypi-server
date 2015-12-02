#!/usr/bin/env python
# encoding: utf-8
from distutils.version import LooseVersion
from functools import total_ordering


@total_ordering
class HashVersion(LooseVersion):
    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        if not isinstance(other, HashVersion):
            other = HashVersion(str(other))

        return tuple(self.version) == tuple(other.version)

    def __gt__(self, other):
        if not isinstance(other, HashVersion):
            other = HashVersion(str(other))

        return tuple(self.version) > tuple(other.version)
