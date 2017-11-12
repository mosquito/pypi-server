FROM alpine
MAINTAINER Mosquito <me@mosquito.su>

ENV ADDRESS=0.0.0.0
ENV PORT=80
ENV STORAGE=/usr/lib/pypi-server
ENV PYPI_SERVER_SRC=/usr/local/src/pypi-server

RUN apk add --no-cache \
    py-mysqldb \
    py-psycopg2 \
    py-curl \
    py-openssl \
    py-cffi \
    py-cparser \
    py-lxml

COPY ./ /tmp

RUN set -ex && \
  apk add --no-cache --virtual .build-deps gcc py-pip python-dev musl-dev && \
  pip --no-cache-dir install '/tmp' && \
  apk del .build-deps

VOLUME "/usr/lib/pypi-server"

COPY docker-entrypoint.py /usr/local/bin/entrypoint.py
RUN chmod a+x /usr/local/bin/entrypoint.py

EXPOSE 80

ENTRYPOINT ["/usr/local/bin/entrypoint.py"]
