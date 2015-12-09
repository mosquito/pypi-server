PYPI Server
===========
Fast asynchronous pypi server implementation.


Features
--------

Supports right now:

* Caching packages from global-pypi
* Serving own packages (registering and updating)
* Password authentication for registering and uploading
* Supports Databases:
    * Postgresql
    * Mysql (mariadb)
    * sqlite3 (default)


Installation
------------

It's simple:

    pip install pypi-server


If you want to support postgres or mysql database:

    pip install 'pypi-server[postgres]' # or 'pypi-server[mysql]'


