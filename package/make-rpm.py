import os
import plumbum
from plumbum.cmd import grep, fpm, ln, sort, find, virtualenv
import logging

log = logging.getLogger()
logging.basicConfig(level=logging.INFO)

ENV_PATH = os.getenv("ENV_PATH", "/usr/share/python/pypi-server")
SRC_PATH = os.getenv("SRC_PATH", "/mnt")

pip = plumbum.local[os.path.join(ENV_PATH, 'bin', 'pip')]
find_requires = plumbum.local['/usr/lib/rpm/find-requires']

log.info("Creating virtualenv %r", ENV_PATH)
virtualenv['-p', 'python2.7', ENV_PATH] & plumbum.FG

log.info("Installing package %r", SRC_PATH)
pip['install', '--no-binary=:all:', '-U', "{}[postgres]".format(SRC_PATH)] & plumbum.FG
pip['install', '--no-binary=:all:', '-U', "{}[proxy]".format(SRC_PATH)] & plumbum.FG
pip['install', '--no-binary=:all:', '-U', "{}[mysql]".format(SRC_PATH)] & plumbum.FG

ln['-snf', os.path.join(ENV_PATH, "bin", "pypi-server"), "/usr/bin/pypi-server"] & plumbum.BG

version = (pip['show', 'pypi-server'] | grep['^Version']) & plumbum.BG
version.wait()

version = version.stdout.strip().replace("Version:", '').strip()

depends = (find[ENV_PATH, '-iname', "*.so"] | find_requires | sort['-u']) & plumbum.BG
depends.wait()

depends = depends.stdout.splitlines()

args = (
    '-s', 'dir',
    '-f', '-t', 'rpm',
    '--iteration', os.getenv('ITERATION', '0'),
    '-n', 'pypi-server',
    '--config-files', '/etc/pypi-server.conf',
    '-v', version,
    '--rpm-dist', 'centos7',
    '-p', "/mnt/dist",
)

for depend in depends:
    args += ('-d', depend)

args += (
    '{0}/={0}/'.format(ENV_PATH),
    '/usr/bin/pypi-server=/usr/bin/pypi-server',
    '/mnt/contrib/pypi-server.conf.example=/etc/pypi-server.conf',
    '/mnt/contrib/pypi-server.service=/usr/lib/systemd/system/pypi-server.service',
)

print(args)

fpm[args] & plumbum.FG
