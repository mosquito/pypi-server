#!/usr/bin/env python2.7
import socket
import os
import sys
import logging
from time import sleep
from distutils import spawn

try:
    from urlparse import urlparse as parse_url
except ImportError:
    from urllib.parse import urlsplit as parse_url

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()


def check_port(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return sock.connect_ex((host, port)) == 0


DEFAULT_PORTS = {
    'postgres': 5432,
    'postgresql': 5432,
    'mysql': 3306,
}


if __name__ == '__main__':
    args = sys.argv[1:]

    if not args or args[0].startswith('-'):
        db_url = parse_url(os.getenv(
            'DB', "sqlite:///var/lib/pypi-server/pypi-server.sqlite3"
        ))
        host = db_url.hostname

        if 'sqlite' in db_url.scheme.lower():
            port = None
        else:
            port = int(db_url.port or DEFAULT_PORTS[db_url.scheme])

        args.insert(0, '/usr/bin/pypi-server')

        while port and not check_port(db_url.hostname, port):
            log.info('Awaiting database...')
            sleep(1)
            continue

        # Ensure database engine is ready
        if port:
            sleep(5)

    executable = args[0]

    if not executable.startswith('/'):
        executable = spawn.find_executable(executable)

    if not executable or not os.path.exists(executable):
        log.error('Command not found')
        exit(127)

    os.execv(executable, args)
