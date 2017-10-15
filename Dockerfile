FROM centos:centos7

COPY dist/pypi-server*.rpm /tmp/
RUN yum localinstall -y /tmp/*.rpm
RUN mkdir -p /usr/lib/pypi-server
RUN yum clean all && rm -fr /tmp/*

ENV ADDRESS=0.0.0.0
ENV PORT=80
ENV STORAGE=/usr/lib/pypi-server

VOLUME "/usr/lib/pypi-server"

ENTRYPOINT /usr/bin/pypi-server

