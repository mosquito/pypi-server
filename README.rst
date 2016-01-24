PYPI Server
===========

.. image:: https://travis-ci.org/mosquito/pypi-server.svg?branch=master
    :target: https://travis-ci.org/mosquito/pypi-server

.. image:: https://img.shields.io/pypi/v/pypi-server.svg
    :target: https://pypi.python.org/pypi/pypi-server/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/wheel/pypi-server.svg
    :target: https://pypi.python.org/pypi/pypi-server/

.. image:: https://img.shields.io/pypi/pyversions/pypi-server.svg
    :target: https://pypi.python.org/pypi/pypi-server/

.. image:: https://img.shields.io/pypi/l/pypi-server.svg
    :target: https://pypi.python.org/pypi/pypi-server/

Fast asynchronous pypi server implementation.

What is this?
-------------

pypi.python.org - is a global package repository of the python packages. This package is a self-hosted pypi service with caching functionallity from the global pypi.

HTTP proxy can't works with XML-RPC of pypi.python.org.

Screenshots
-----------

.. image:: screenshots/packages.png?raw=true
   :scale: 50 %

.. image:: screenshots/users.png?raw=true
   :scale: 50 %

.. image:: screenshots/create_user.png?raw=true
   :scale: 50 %


Features
--------

Supports right now:

* Caching packages from global-pypi
* Serving own packages (registering and updating)
* Password authentication for registering and uploading
* Supported Databases:
    * Postgresql
    * Mysql (mariadb)
    * sqlite3 (default)


Installation
------------

First prepare you system.

Centos:

.. code-block:: bash

    # Install compillers
    yum groupinstall -y "Development tools"

    # Install dependency headers
    yum install -y python-pip python-devel libxml2-devel libxslt-devel libffi-devel

    # Install the database library headers (if you use postgresql)
    yum install -y libpqxx-devel


Debian (Ubuntu):

.. code-block:: bash

    # Install compillers
    apt-get install -y build-essential
    apt-get install -y python-dev python-pip libxml2-dev libxslt-dev libffi-dev
    apt-get install -y libpq-dev



Install pypi-server:

.. code-block:: bash

    pip install pypi-server


If you want to support postgres or mysql database:

.. code-block:: bash

    pip install 'pypi-server[postgres]' # or 'pypi-server[mysql]'

