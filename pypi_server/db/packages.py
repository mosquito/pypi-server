#!/usr/bin/env python
# encoding: utf-8
import hashlib
import datetime

from multiprocessing import RLock

import os
import peewee as p
from playhouse.kv import JSONField
from . import Model, DB
from .users import Users
from ..hash_version import HashVersion

try:
    import cPickle as pickle
except ImportError:
    import pickle


class File(file):
    __slots__ = ('__close_callbacks',)

    def __init__(self, name, mode='rb'):
        self.__close_callbacks = set()
        super(File, self).__init__(name, mode)

    def add_close_callback(self, cb):
        self.__close_callbacks.add(cb)

    def close(self):
        super(File, self).close()
        for cb in list(self.__close_callbacks):
            try:
                cb(self)
            except:
                pass


class VersionField(p.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.pop('max_length', 25)
        super(VersionField, self).__init__(*args, **kwargs)

    def python_value(self, value):
        return HashVersion(value) if value else None

    def db_value(self, value):
        return super(VersionField, self).db_value(str(value))


class FileField(p.CharField):
    STORAGE = None

    def python_value(self, value):
        abs_path = os.path.join(self.STORAGE, value)
        return os.path.join(abs_path)

    def db_value(self, value):
        return super(FileField, self).db_value(
            str(os.path.relpath(value, self.STORAGE))
        )


class Package(Model):
    name = p.CharField(index=True)
    lower_name = p.CharField(index=True, unique=True)
    owner = p.ForeignKeyField(Users, null=True, index=True)
    stable_version = VersionField(null=True)
    is_proxy = p.BooleanField(default=False, null=False)

    def versions(self, show_hidden=False):
        return PackageVersion.select(
            PackageVersion.version,
            PackageVersion.package,
        ).where(
            PackageVersion.package == self,
            PackageVersion.hidden == show_hidden
        ).order_by(PackageVersion.version.desc())

    def find_version(self, name):
        return PackageVersion.get(
            PackageVersion.package == self,
            PackageVersion.version == HashVersion(name),
        )

    def create_version(self, name):
        with DB.transaction():
            q = PackageVersion.select(
                PackageVersion.id
            ).where(
                PackageVersion.package == self,
                PackageVersion.version == name
            ).limit(1)

            if q.count():
                return PackageVersion.get(id=q[0].id)

            version = PackageVersion(
                package=self,
                version=name if isinstance(name, HashVersion) else HashVersion(name),
            )

            version.save()

        return version

    @classmethod
    def get_or_create(cls, name, proxy=False):
        if not Package.select().where(Package.name == name).count():
            pkg = Package(name=name, lower_name=name.lower(), is_proxy=proxy, owner=None)
            pkg.save()
            return pkg

        return Package.get(name=name)


class PackageVersion(Model):
    package = p.ForeignKeyField(Package, index=True, null=False)
    version = VersionField(index=True, null=False)
    hidden = p.BooleanField(default=False, null=False, index=True)
    downloads = p.IntegerField(default=0, index=True)
    author = p.CharField(max_length=255, null=True)
    author_email = p.CharField(max_length=255, null=True)
    maintainer = p.CharField(max_length=255, null=True)
    maintainer_email = p.CharField(max_length=255, null=True)
    home_page = p.CharField(max_length=256, null=True)
    license = p.CharField(max_length=128, null=True)
    summary = p.CharField(max_length=255, null=True)
    description = p.TextField(null=True)
    keywords = JSONField(default=[])
    platform = p.CharField(max_length=255, null=True)
    download_url = p.CharField(max_length=255, null=True)
    classifiers = JSONField(default=[])
    requires = JSONField(default=[])
    requires_dist = JSONField(default=[])
    provides = JSONField(default=[])
    provides_dist = JSONField(default=[])
    requires_external = JSONField(default=[])
    requires_python = p.CharField(max_length=255, null=True)
    obsoletes = JSONField(default=[])
    obsoletes_dist = JSONField(default=[])
    project_url = p.CharField(max_length=255, null=True)

    def files(self):
        return PackageFile.select().where(
            PackageFile.package == self.package,
            PackageFile.version == self
        )

    def find_file(self, name):
        return PackageFile.select().where(PackageFile.basename == name)

    def create_file(self, name):
        name = os.path.basename(name)
        pkg_file = PackageFile(
            package=self.package,
            version=self,
            basename=name,
            file=os.path.join(
                PackageFile.file.STORAGE,
                self.package.name,
                str(self.version),
                name
            )
        )

        pkg_file.save()
        return pkg_file

    def update_metadata(self, metadata):
        print (metadata)


class PackageFile(Model):
    LOCK = RLock()
    CHUNK_SIZE = 2 ** 16

    file = FileField(index=True, max_length=255)
    basename = p.CharField(max_length=255, index=True)
    ts = p.DateTimeField(null=True)
    md5 = p.CharField(max_length=32, null=True)
    size = p.IntegerField(null=True)
    package = p.ForeignKeyField(Package, index=True)
    version = p.ForeignKeyField(PackageVersion, index=True)

    @classmethod
    def set_storage(cls, path):
        cls.file.STORAGE = path

    def exists(self):
        return os.path.exists(self.file) and not os.path.isdir(self.file)

    def open(self, mode='rb'):
        dirname = os.path.dirname(self.file)

        with self.LOCK:
            if not os.path.exists(dirname):
                os.makedirs(dirname)

        f = File(self.file, mode)

        def metadata_update(f):
            stat = os.stat(self.file)
            self.ts = datetime.datetime.fromtimestamp(stat.st_mtime)
            self.size = stat.st_size

            md5 = hashlib.md5()
            with open(self.file, 'rb') as fl:
                data = fl.read(self.CHUNK_SIZE)
                md5.update(data)
                while data:
                    data = fl.read(self.CHUNK_SIZE)
                    md5.update(data)

                    self.md5 = md5.hexdigest()

            self.save()

        if any(x in mode for x in 'wa'):
            f.add_close_callback(metadata_update)

        return f
