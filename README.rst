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

HTTP proxy can't work with XML-RPC of pypi.python.org.

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

Use `docker image`_ and following `docker-compose.yml`_ (uses postgresql):

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
          - ./packages:/var/lib/pypi-server
        environment:
          # Database URL. Use `sqlite3:///` or `mysql://` when needed
          DB: "postgres://pypi-server:pypi-server@db/pypi-server"

          ## By default random
          #SECRET: changeme

          ## Override standard port
          #PORT: 80

          ## Set "X-Headers" (e.g. X-Forwarded-For)
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

Use prepared Centos 7 rpm from `releases`_.

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

Use prepared deb files from `releases`_.

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


How to upload your own package
---------------------------

1. Make sure that your package setup.py file is correct. Check reference at https://packaging.python.org/distributing/

2. Create at home directory .pypirc (Note: If your pypi-server is running at http://pip.example.com:8088, the upload URL will be http://pip.example.com:8088/pypi)

.. code-block::

    [distutils]
    index-servers =
        mypypi

    [mypypi]
    repository=http://pip.example.com:8088/pypi
    username=admin
    password=admin

3. Make bundle, register package at your pypi-server and upload package:

.. code-block:: bash

    cd your_package_root_folder
    python setup.py sdist register upload -r mypypi


How to download your package
----------------------------

.. code-block:: bash

    pip install -i http://pip.example.com:8088/simple --trusted-host pip.example.com  my-package-name
    
If you want to configure pip to always pull from http://pip.example.com:8088 (which, since pypi-server proxies to pypi.org if it doesn't have a package, probably is what you want to do), you can make a `pip.conf`

.. code-block:: bash

    cat ~/.pip/pip.conf
    [global]
    index-url = http://pip.example.com:8088/simple/

If you don't have an SSL cert for your PyPi server, you probably want to also tell pip to trust that domain anyway,

.. code-block:: bash

    cat ~/.pip/pip.conf
    [global]
    index-url = http://pip.example.com:8088/simple/
    
    [install]
    trusted-host=pip.example.com

.. _releases: https://github.com/mosquito/pypi-server/releases/
.. _docker image: https://hub.docker.com/r/mosquito/pypi-server/
.. _docker-compose.yml: https://github.com/mosquito/pypi-server/blob/master/docker-compose.yml
