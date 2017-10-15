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
    * sqlite3 (only for development)


Installation
------------

Docker
++++++

Use docker-compose with postgresql:

.. code-block:: yaml

    version: '2'

    services:
      db:
        image: postgres
        environment:
          POSTGRES_PASSWORD: pypi-server
          POSTGRES_USER: pypi-server
          POSTGRES_DB: pypi-server
        volumes:
          - ./postgresql:/var/lib/postgresql/data

      pypi_server:
        image: mosquito/pypi-server:latest
        links:
          - db
        restart: always
        ports:
          - 8080:80
        volumes:
          - ./packages:/usr/lib/pypi-server
        environment:
          # Database URL. Use `sqlite3:///` or `mysql://` when needed
          DB: "postgres://pypi-server:pypi-server@db/pypi-server"

          ## By default random
          #SECRET: changeme

          ## Override standard port
          #PORT: 80

          ## Set "X-Headers" for nginx (e.g. X-Accel-Expires)
          #PROXY_MODE: 1

          ## Set 0 when you want to disable proxying from global pypi
          #PYPI_PROXY: 1

          ## Tread-pool size (default cpu_count * 2)
          #POOL_SIZE: 4

          ## Maximum proxy clients count
          #MAX_CLIENTS: 25

          ## PYPI server url
          #PYPY_SERVER: https://pypi.python.org


Centos
++++++

Use prepared Centos 7 rpm from releases.

Manual installation:

.. code-block:: bash

    # Install compillers
    yum groupinstall -y "Development tools"

    # Install dependency headers
    yum install -y python-pip python-devel libxml2-devel libxslt-devel libffi-devel

    # Install the database library headers (if you use postgresql)
    yum install -y libpqxx-devel


Debian (Ubuntu)
+++++++++++++++

Use prepared deb files from releases.

Manual installation:

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

Default admin login \ password is: admin \ admin


How upload your own package
---------------------------

1. Make sure what your package setup.py file is correct. Check reference at https://packaging.python.org/distributing/

2. Create at home directory .pypirc

.. code-block::

    [distutils]
    index-servers =
        mypypi

    [mypypi]
    repository=http://example.com/pypi
    username=admin
    password=admin

3. Make bundle, register package at your pypi-server and upload package:

.. code-block:: bash

    cd your_package_root_folder
    python setup.py sdist register upload -r mypypi
