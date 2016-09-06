# encoding: utf-8
import base64
import hashlib
import logging
import peewee
from functools import wraps
from peewee import DoesNotExist
from pypi_server import PY2
from pypi_server.db import DB
from pypi_server.handlers.pypi.proxy.client import PYPIClient
from six import b
from tornado.gen import coroutine, Task, maybe_future, Return
from tornado.web import asynchronous, HTTPError
from tornado.httpclient import AsyncHTTPClient, HTTPError as HTTPClientError
from pypi_server.handlers import route
from pypi_server.handlers.base import BaseHandler, threaded
from pypi_server.http_cache import HTTPCache
from pypi_server.cache import Cache, HOUR, MONTH
from pypi_server.db.packages import Package, PackageVersion, PackageFile, HashVersion
from pypi_server.db.users import Users


if PY2:
    from urllib import unquote_plus
else:
    from urllib.parse import unquote_plus


log = logging.getLogger(__name__)


@threaded
def write_file(pkg_file, data):
    with pkg_file.open('wb+') as f:
        f.write(data)

    pkg_file.fetched = True

    assert hashlib.md5(data).hexdigest() == pkg_file.md5

    pkg_file.save()
    return pkg_file


@route(r"/simple/(?P<package>\S+)/(?P<version>\S+)/(?P<filename>\S+)")
@route(r"/package/(?P<package>\S+)/(?P<version>\S+)/(?P<filename>\S+)")
class FileHandler(BaseHandler):
    CHUNK_SIZE = 2 ** 16

    @asynchronous
    @HTTPCache(MONTH, use_expires=True, expire_timeout=MONTH)
    @coroutine
    def get(self, package, version, filename):
        try:
            package = yield PYPIClient.find_real_name(package)
        except (LookupError, HTTPClientError) as e:
            if isinstance(e, HTTPClientError):
                log.warning("PYPI backend return an error: %s", e)

            package = yield self.thread_pool.submit(Package.find, package)

        try:
            pkg_file = yield self.find_file(package, version, filename)
            if not pkg_file.fetched:
                yield self.fetch_remote_file(pkg_file)
        except LookupError:
            self.send_error(404)
        else:
            self.set_header("MD5", pkg_file.md5)
            self.set_header("ETag", pkg_file.md5)
            self.set_header("Content-Length", pkg_file.size)
            self.set_header("Content-Type", 'application/octet-stream')
            self.set_header("Date", pkg_file.ts.strftime("%a, %d %b %Y %H:%M:%S %Z"))

            with pkg_file.open() as f:
                reader = threaded(f.read)

                data = yield reader(self.CHUNK_SIZE)
                self.write(data)
                yield Task(self.flush)

                while data:
                    data = yield reader(self.CHUNK_SIZE)
                    self.write(data)
                    yield Task(self.flush)

            self.finish()

    @threaded
    def find_file(self, package, version, filename):
        if not isinstance(package, Package):
            package = Package.find(package)

        pkg_file = PackageFile.select(
            PackageFile.id
        ).join(
            Package
        ).join(
            PackageVersion
        ).where(
            PackageFile.package == package,
            PackageFile.basename == filename,
            PackageVersion.version == HashVersion(version),
        ).limit(1)

        if not pkg_file.count():
            raise LookupError("Not found")

        return PackageFile.get(id=pkg_file[0].id)

    @classmethod
    @coroutine
    def fetch_remote_file(cls, pkg_file):
        response = yield AsyncHTTPClient().fetch(pkg_file.url)
        yield write_file(pkg_file, response.body)


@threaded
def check_password(login, password):
    try:
        user = Users.check(login, password)
    except DoesNotExist:
        raise LookupError('User not found')

    return user


def authorization_required(func):
    @wraps(func)
    @coroutine
    def wrap(self, *args, **kwargs):
        auth_header = self.request.headers.get('Authorization')
        if not auth_header:
            self.set_header('WWW-Authenticate', 'Basic realm="pypi"')
            self.set_status(401)
            raise Return(self.finish("Authorization required"))

        auth_type, data = auth_header.split()
        if auth_type.lower() != 'basic':
            raise Return(self.send_error(400))

        username, password = map(lambda x: unquote_plus(x.decode("utf-8")), base64.b64decode(b(data)).split(b(":")))
        try:
            self.current_user = yield check_password(username, password)
        except LookupError:
            raise HTTPError(403)

        result = yield maybe_future(func(self, *args, **kwargs))
        raise Return(result)

    return wrap


@route(r"/pypi/?")
class XmlRPC(BaseHandler):
    METADATA_KEYS = {
        u"name",
        u"version",
        u"stable_version",
        u"author",
        u"author_email",
        u"maintainer",
        u"maintainer_email",
        u"home_page",
        u"license",
        u"summary",
        u"description",
        u"keywords",
        u"platform",
        u"download_url",
        u"classifiers",
        u"requires",
        u"requires_dist",
        u"provides",
        u"provides_dist",
        u"requires_external",
        u"requires_python",
        u"obsoletes",
        u"obsoletes_dist",
        u"project_url",
    }

    @coroutine
    def prepare(self):
        if self.request.method.upper() == 'POST' and not self.request.body.startswith(b("\r\n")):
            boundary = dict(
                filter(
                    lambda x: x[0] == 'boundary',
                    map(
                        lambda x: x.strip().split("="),
                        self.request.headers.get('Content-Type', '').split(';')
                    )
                )
            ).get('boundary')

            if not boundary:
                raise HTTPError(400)

            def normalize(chunk):
                if b('\n\n') not in chunk:
                    return b('\r\n') + chunk[1:]

                ret = b('')
                ret += b('\r\n')
                data, content = chunk.split(b('\n\n'), 1)
                ret += data[1:]
                ret += b('\r\n\r\n')
                ret += content[:-1]
                ret += b('\r\n')
                return ret

            boundary = b("--{0}".format(boundary))

            new_body = boundary.join(
                map(
                    normalize,
                    self.request.body.split(boundary)
                )
            )

            new_body = new_body[:-4]
            new_body += b('--\r\n')

            self.request.body = new_body
            self.request._parse_body()

        yield maybe_future(super(XmlRPC, self).prepare())

    @coroutine
    def post(self):
        try:
            action = self.get_body_argument(':action')
            self.request.body_arguments.pop(':action')

            log.debug("Request to call action: %s", action)
            method = getattr(self, "action_{0}".format(action), self._action_not_found)
        except:
            raise HTTPError(400)

        log.info("Calling action: %s", action)
        yield maybe_future(method())

    @staticmethod
    def _action_not_found():
        raise HTTPError(400)

    @authorization_required
    @threaded
    def action_submit(self):
        name = self.get_body_argument('name')

        q = Package.select().where(
            Package.name == name,
            Package.owner == self.current_user
        )

        if q.count():
            raise HTTPError(409)

        if not self.current_user.is_admin:
            q = Package.select().where(
                Package.name == name,
                Package.owner != self.current_user
            )

            if q.count():
                raise HTTPError(403)

        pkg = Package(name=name, lower_name=name.lower(), owner=self.current_user)
        pkg.save()

    def action_verify(self):
        pass

    @authorization_required
    @threaded
    def action_file_upload(self):
        with DB.transaction():
            package_name = self.get_body_argument('name').lower()

            if not Package.select().where(Package.lower_name == package_name).count():
                raise HTTPError(404)

            package = Package.get(lower_name=package_name)
            version = package.create_version(self.get_body_argument('version'))

            uploaded_file = self.request.files['content'][0]
            if not str(hashlib.md5(uploaded_file.body).hexdigest()) == str(self.get_body_argument('md5_digest')):
                raise HTTPError(406)

            list_values = (u'classifiers', u'keywords')
            for key in self.METADATA_KEYS:
                val = self.get_body_argument(key, 'UNKNOWN')
                if key in list_values and not isinstance(val, (list, tuple)):
                    val = [val]

                setattr(version, key, val)

            version.save()

            try:
                pkg_file = version.create_file(uploaded_file.filename)
                pkg_file.fetched = True
                pkg_file.md5 = str(self.get_body_argument('md5_digest'))

                if pkg_file.exists():
                    raise HTTPError(409)

                with pkg_file.open("wb+") as f:
                    f.write(uploaded_file.body)

                pkg_file.save()
            except peewee.DataError:
                raise HTTPError(409)
