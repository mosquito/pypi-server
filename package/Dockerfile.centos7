FROM mosquito/fpm:centos7

RUN yum install -y epel-release
RUN yum install -y python-pip python-devel make gcc
RUN pip install -U pip virtualenv sh plumbum
RUN yum install -y \
    libcurl-devel \
    libcurl-openssl-devel \
    libffi-devel \
    libpqxx-devel \
    libxml2-devel \
    libxslt-devel \
    mariadb-devel \
    openssl-devel \
    postgresql-devel

ENV PYCURL_SSL_LIBRARY=openssl