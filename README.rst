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

First prepare you system.

Centos:

    # Install compillers
    yum groupinstall -y "Development tools"

    # Install dependency headers
    yum install -y python-pip python-devel libxml2-devel libxslt-devel libffi-devel

    # Install the database library headers (if you use postgresql)
    yum install -y libpqxx-devel


Debian (Ubuntu):

    # Install compillers
    apt-get install -y build-essential
    apt-get install -y python-dev python-pip libxml2-dev libxslt-dev libffi-dev
    apt-get install -y libpq-dev



Install pypi-server:

    pip install pypi-server


If you want to support postgres or mysql database:

    pip install 'pypi-server[postgres]' # or 'pypi-server[mysql]'


