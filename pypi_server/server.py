# encoding: utf-8
import uuid
import errno
import signal
import pwd
import os
from slimurl import URL
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.log import gen_log as log
from tornado.options import options, define
from tornado.process import cpu_count
from tornado.concurrent import futures
from tornado.web import Application
from tornado.httpclient import AsyncHTTPClient
from tornado.ioloop import PeriodicCallback
from pypi_server import ROOT
from pypi_server.handlers.pypi.proxy.client import PYPIClient
from pypi_server.db import init_db
from pypi_server.db.packages import PackageFile
from pypi_server import handlers


define('config', help="Configuration file")

define("address", help="Listen address (default 127.0.0.1) [ENV:ADDRESS]",
       default=os.getenv('ADDRESS', "127.0.0.1"))

define("port", help="Listen port (default 8080) [ENV:PORT]",
       type=int, default=int(os.getenv('PORT', '8080')))

define("debug", help="Use for attach a debugger",
       default=bool(os.getenv("DEBUG")), type=bool)

define("gzip", help="Compress responses (default False) [ENV:GZIP]",
       default=bool(os.getenv("GZIP", '0')), type=bool)

define("proxy-mode", help="Process X-headers on requests (default True) [ENV:PROXY_MODE]",
       default=bool(os.getenv('PROXY_MODE', '1')), type=bool)

define("pool-size", help="Thread pool size (default cou_count * 2) [ENV:POOL_SIZE]",
       type=int, default=int(os.getenv('POOL_SIZE', cpu_count() * 2)))

define("secret", help="Cookie secret (default random) [ENV:SECRET]",
       default=os.getenv("SECRET", uuid.uuid4().bytes))

define("user", help="Change UID of current process (not change by default)", default=None)

define(
    "storage", help="Packages storage (default $CWD/packages) [ENV:STORAGE]", type=str,
    default=os.path.abspath(
        os.getenv(
            "STORAGE",
            os.path.join(os.path.abspath(os.path.curdir), 'packages')
        )
    )
)

define(
    "database", help="Application database (default sqlite:///{storage}/metadata.db) [ENV:DB]",
    type=URL,
    default=os.getenv(
        "DB",
        URL(
            "sqlite://{0}".format("/".join(
                os.path.split(os.path.join(os.path.abspath(os.path.curdir), 'packages', 'metadata.db'))
            ))
        )
    )
)

define("max_http_clients",
       help="Maximum HTTP Client instances for proxy requests (default 25) [ENV:MAX_CLIENTS]",
       default=int(os.getenv("MAX_CLIENTS", '25')), type=int)

define("pypi_server",
       help="PYPI service url. Using for proxy. (default https://pypi.python.org/) [ENV:PYPY_SERVER]",
       default=URL(os.getenv("PYPI_SERVER", 'https://pypi.python.org/')), type=URL)


def run():
    options.parse_command_line()

    if options.config:
        options.parse_config_file(options.config)

    options.storage = os.path.abspath(options.storage)

    if os.getuid() == 0 and options.user:
        pw = pwd.getpwnam(options.user)
        uid, gid = pw.pw_uid, pw.pw_gid
        log.info("Changind user to %s [%s:%s]", options.user, uid, gid)
        os.setgid(uid)
        os.setuid(uid)

    try:
        if not all(f(options.storage) for f in (os.path.exists, os.path.isdir)):
            log.info('Creating new package storage directory: "%s"', options.storage)
            os.makedirs(options.storage)

        def on_interrupt(*args):
            log.warning("Receiving interrupt signal. Application will be stopped.")
            exit(errno.EINTR)

        log.debug("Preparing signal handling")
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGQUIT):
            signal.signal(sig, on_interrupt)

        log.debug("Creating application instance")
        app = Application(
            base_dir=ROOT,
            debug=options.debug,
            reload=options.debug,
            cookie_secret=options.secret,
            template_path=os.path.join(ROOT, 'templates'),
            default_handler_class=handlers.DefaultHandler,
            gzip=options.gzip,
            handlers=handlers.ROUTES,
            options=options
        )

        log.debug("Creating IOLoop instance.")
        io_loop = IOLoop.current()

        io_loop.run_sync(lambda: init_db(options.database))

        log.info("Init thread pool with %d threads", options.pool_size)
        handlers.base.BaseHandler.THREAD_POOL = futures.ThreadPoolExecutor(options.pool_size)

        AsyncHTTPClient.configure(None, max_clients=options.max_http_clients)

        PYPIClient.configure(
            options.pypi_server,
            handlers.base.BaseHandler.THREAD_POOL
        )

        pypi_updater = PeriodicCallback(PYPIClient.packages, 300000, io_loop)

        io_loop.add_callback(PYPIClient.packages)
        io_loop.add_callback(pypi_updater.start)

        log.info("Starting server http://%s:%d/", options.address, options.port)
        http_server = HTTPServer(app, xheaders=options.proxy_mode)
        http_server.listen(options.port, address=options.address)

        log.debug('Setting "%s" as storage', options.storage)
        PackageFile.set_storage(options.storage)

        log.debug("Starting main loop")
        io_loop.start()
    except Exception as e:
        log.fatal("Exception on main loop:")
        log.exception(e)
        exit(1)
    else:
        exit(0)


if __name__ == '__main__':
    run()
