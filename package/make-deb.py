import os
from subprocess import check_output
import plumbum
from plumbum.cmd import grep, fpm, ln, sort, find, virtualenv
import logging

log = logging.getLogger()
logging.basicConfig(level=logging.INFO)

ENV_PATH = os.getenv("ENV_PATH", "/usr/share/python3/pypi-server")
SRC_PATH = os.getenv("SRC_PATH", "/mnt")

pip = plumbum.local[os.path.join(ENV_PATH, 'bin', 'pip3')]

log.info("Creating virtualenv %r", ENV_PATH)
virtualenv['-p', 'python3', ENV_PATH] & plumbum.FG

log.info("Installing package %r", SRC_PATH)
pip['install', '--no-binary=:all:', '-U', "{}[postgres]".format(SRC_PATH)] & plumbum.FG
pip['install', '--no-binary=:all:', "{}[proxy]".format(SRC_PATH)] & plumbum.FG
pip['install', '--no-binary=:all:', "{}[mysql]".format(SRC_PATH)] & plumbum.FG

ln['-snf', os.path.join(ENV_PATH, "bin", "pypi-server"), "/usr/bin/pypi-server"] & plumbum.BG

version = (pip['show', 'pypi-server'] | grep['^Version']) & plumbum.BG
version.wait()

version = version.stdout.strip().replace("Version:", '').strip()

args = (
    '-s', 'dir',
    '-f', '-t', 'deb',
    '--iteration', os.getenv('ITERATION', '0'),
    '-n', 'pypi-server',
    '--config-files', '/etc/pypi-server.conf',
    '--deb-systemd', '/mnt/contrib/pypi-server.service',
    '-v', version,
    '-p', "/mnt/dist",
    '-d', 'python3',
    '-d', 'python3-distutils',
)

depends = check_output((
    'find %s -iname "*.so" -exec ldd {} \; | '
    '''awk '{print $1}' | '''
    'sort -u | '
    'xargs dpkg -S | '
    '''awk '{print $1}' | '''
    'sort -u | '
    '''cut -d ':' -f1 | sort -u'''
) % ENV_PATH, shell=True).decode('utf-8').splitlines()

for depend in depends:
    args += ('-d', depend)

args += (
    '{0}/={0}/'.format(ENV_PATH),
    '/usr/bin/pypi-server=/usr/bin/pypi-server',
    '/mnt/contrib/pypi-server.conf.example=/etc/pypi-server.conf',
)

fpm[args] & plumbum.FG
