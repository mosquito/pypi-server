#################################################################
####################### BUILD STAGE #############################
#################################################################
# This image contains:
# 1. All the Python versions
# 2. required python headers
# 3. C compiler and developer tools
FROM snakepacker/python:all as builder

MAINTAINER Mosquito <me@mosquito.su>

RUN apt-install libcurl-openssl1.0-dev libmysqlclient-dev libpq-dev \
    libssl1.0-dev libxml2-dev libxslt1-dev libffi-dev

ADD dist/*.whl /tmp

# Create virtualenv on python 3.10
# Target folder should be the same on the build stage and on the target stage
RUN virtualenv -p python3.10 /usr/share/python3/app

# Install target package
RUN /usr/share/python3/app/bin/pip install -U /tmp/*.whl

# Will be find required system libraries and their packages
RUN find-libdeps /usr/share/python3/app > /usr/share/python3/app/pkgdeps.txt

#################################################################
####################### TARGET STAGE ############################
#################################################################
# Use the image version used on the build stage
FROM snakepacker/python:3.10

# Copy virtualenv to the target image
COPY --from=builder /usr/share/python3/app /usr/share/python3/app

# Install the required library packages
RUN xargs -ra /usr/share/python3/app/pkgdeps.txt apt-install

# Create a symlink to the target binary (just for convenience)
RUN ln -snf /usr/share/python3/app/bin/pypi-server /usr/bin/

VOLUME "/var/lib/pypi-server"
