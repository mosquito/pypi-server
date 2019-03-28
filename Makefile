COMMIT = $(shell git rev-parse --verify HEAD | cut -c1-8)
VERSION = $(shell python setup.py --version)

all: docker-image rpm deb

rpm: rpm-image
	docker run --rm -t \
	    -v $(PWD):/mnt \
	    -v /tmp/pip-cache-centos:/root/.cache/pip \
	    -e ITERATION=$(COMMIT) \
	    pypi-server:centos7 python /mnt/package/make-rpm.py

deb: deb-deb8 deb-deb9 deb-xenial deb-bionic

deb-deb8: deb8-image
	docker run --rm -t \
	    -v $(PWD):/mnt \
	    -v /tmp/pip-cache-debian:/root/.cache/pip \
	    -e ITERATION=debian8-$(COMMIT) \
	    pypi-server:debian8 python3 /mnt/package/make-deb.py

deb-deb9: deb9-image
	docker run --rm -t \
		-v $(PWD):/mnt \
		-v /tmp/pip-cache-debian:/root/.cache/pip \
		-e ITERATION=debian9-$(COMMIT) \
		pypi-server:debian9 python3 /mnt/package/make-deb.py

deb-xenial: xenial-image
	docker run --rm -t \
	    -v $(PWD):/mnt \
	    -v /tmp/pip-cache-debian:/root/.cache/pip \
	    -e ITERATION=xenial-$(COMMIT) \
	    pypi-server:xenial python3 /mnt/package/make-deb.py

deb-bionic: bionic-image
	docker run --rm -t \
		-v $(PWD):/mnt \
		-v /tmp/pip-cache-debian:/root/.cache/pip \
		-e ITERATION=bionic-$(COMMIT) \
		pypi-server:bionic python3 /mnt/package/make-deb.py


rpm-image:
	docker build -t pypi-server:centos7 -f package/Dockerfile.centos7 package

deb8-image:
	docker build -t pypi-server:debian8 -f package/Dockerfile.debian8 package

deb9-image:
	docker build -t pypi-server:debian9 -f package/Dockerfile.debian9 package

xenial-image:
	docker build -t pypi-server:xenial -f package/Dockerfile.xenial package

bionic-image:
	docker build -t pypi-server:bionic -f package/Dockerfile.bionic package

docker-image:
	docker build -t mosquito/pypi-server:$(VERSION) --squash .
	docker tag mosquito/pypi-server:$(VERSION)  mosquito/pypi-server:latest
