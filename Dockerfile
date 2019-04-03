FROM snakepacker/python:all as builder

MAINTAINER Mosquito <me@mosquito.su>

RUN apt-get update && \
    apt-get install -y \
        libcurl-openssl1.0-dev \
        libmysqlclient-dev \
        libpq-dev \
        libssl1.0-dev \
        libxml2-dev \
        libxslt1-dev \
        libffi-dev

RUN virtualenv -p python3.7 /usr/share/python/app

RUN /usr/share/python/app/bin/pip install -U \
    pypi-server[postgres] \
    pypi-server[mysql] \
    pypi-server[proxy]

COPY docker-entrypoint.py /usr/share/python/app/bin/entrypoint.py

RUN chmod a+x /usr/share/python/app/bin/entrypoint.py

#################################################################
FROM snakepacker/python:3.7

RUN apt-get update && \
    apt-get install -y \
        libcurl3 \
        libmysqlclient20 \
        libpq5 \
        libssl1.0.0 \
        libxml2 \
        libxslt1.1 \
        libffi6 && \
    apt-get clean && \
    rm -fr /var/lib/apt/lists/*

ENV ADDRESS=0.0.0.0
ENV PORT=80
ENV STORAGE=/var/lib/pypi-server

EXPOSE 80

COPY --from=builder /usr/share/python/app /usr/share/python/app
RUN ln -snf /usr/share/python/app/bin/entrypoint.py /usr/bin/ && \
    ln -snf /usr/share/python/app/bin/pypi-server /usr/bin/

ENTRYPOINT /usr/bin/entrypoint.py
VOLUME "/var/lib/pypi-server"
