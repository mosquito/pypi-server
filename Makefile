COMMIT = $(shell git rev-parse --verify HEAD | cut -c1-8)

all: rpm deb

rpm: rpm-image
	docker run --rm -t \
	    -v $(PWD):/mnt \
	    -v /tmp/pip-cache-centos:/root/.cache/pip \
	    -e ITERATION=$(COMMIT) \
	    pypi-server:centos7 python /mnt/package/make-rpm.py

deb: deb8-image ubuntu-image
	docker run --rm -t \
	    -v $(PWD):/mnt \
	    -v /tmp/pip-cache-debian:/root/.cache/pip \
	    -e ITERATION=debian8-$(COMMIT) \
	    pypi-server:debian8 python3 /mnt/package/make-deb.py

	docker run --rm -t \
	    -v $(PWD):/mnt \
	    -v /tmp/pip-cache-debian:/root/.cache/pip \
	    -e ITERATION=xenial-$(COMMIT) \
	    pypi-server:ubuntu python3 /mnt/package/make-deb.py



rpm-image:
	docker build -t pypi-server:centos7 -f package/Dockerfile.centos7 package

deb8-image:
	docker build -t pypi-server:debian8 -f package/Dockerfile.debian8 package

ubuntu-image:
	docker build -t pypi-server:ubuntu -f package/Dockerfile.ubuntu package
