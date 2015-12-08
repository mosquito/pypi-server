#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import, print_function
import os
import pypi_server
from setuptools import setup, find_packages


REQUIREMENTS = (
    'tornado>=4.3',
    'tornado-xmlrpc',
    'slimurl',
    'peewee',
    'bcrypt',
    'lxml',
    'futures',
)


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
        ("/etc", (os.path.join('contrib', 'pypi-server.conf'),))
    )


setup(
    name='pypi-server',
    version=pypi_server.__version__,
    author=pypi_server.__author__,
    license="MIT",
    description="Tornado PyPi server",
    long_description=open('README.rst').read(),
    platforms="all",
    classifiers=[
        'Environment :: Console',
        'Programming Language :: Python',
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
    install_requires=REQUIREMENTS,
    extras_require={
        'mysql': ['mysql-python'],
        'postgres': ['psycopg2'],
    }
)
