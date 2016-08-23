#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import, print_function
import os
import pypi_server
from setuptools import setup, find_packages


def walker(base, *paths):
    file_list = set([])
    cur_dir = os.path.abspath(os.curdir)

    os.chdir(base)
    try:
        for path in paths:
            for dname, dirs, files in os.walk(path):
                for f in files:
                    file_list.add(os.path.join(dname, f))
    finally:
        os.chdir(cur_dir)

    return list(file_list)


data_files = ()

if os.geteuid() == 0:
    data_files = (
        ("/etc/systemd/system", (os.path.join('contrib', 'pypi-server.service'),)),
        ("/etc", (os.path.join('contrib', 'pypi-server.conf.example'),))
    )


setup(
    name='pypi-server',
    version=pypi_server.__version__,
    author=pypi_server.__author__,
    author_email=", ".join(map(lambda x: x[1], pypi_server.author_info)),
    url="https://github.com/mosquito/pypi-server/",
    license="MIT",
    description="Tornado PyPi server",
    long_description=open('README.rst').read(),
    platforms="all",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Communications :: Email',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Software Development',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Version Control',
        'Topic :: System',
        'Topic :: System :: Software Distribution',
    ],
    include_package_data=True,
    zip_safe=False,
    package_data={
        'pypi_server': walker(os.path.dirname(pypi_server.__file__), 'static', 'templates'),
    },
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'pypi-server = pypi_server.server:run',
        ],
    },
    packages=find_packages(exclude=('tests',)),
    install_requires=(
        'tornado>=4.3',
        'tornado-xmlrpc',
        'slimurl',
        'peewee<2.8',
        'bcrypt>=2.0',
        'lxml',
        'futures',
        'six',
    ),
    extras_require={
        'mysql': ['mysql-python'],
        'postgres': ['psycopg2'],
    }
)
