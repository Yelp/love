.PHONY: all test clean run-dev deploy deploy_with_dispatch deploy_build

all: test

run-dev: config.py lib
	dev_appserver.py dispatch.yaml app.yaml worker.yaml

deploy: deploy_build
	appcfg.py --no_cookies update app.yaml worker.yaml

deploy_with_dispatch: deploy_build
	appcfg.py --no_cookies update app.yaml worker.yaml dispatch.yaml

deploy_build: config.py clean lib test
	@echo "\033[31mHave you bumped the app version? Hit ENTER to continue, CTRL-C to abort.\033[0m"
	@read ignored

lib: requirements.txt
	mkdir -p lib
	rm -rf lib/*
	pip install -r requirements.txt -t lib

test: google_appengine
	# reset database before each test run
	rm -f /tmp/nosegae.sqlite3
	tox

clean:
	find . -name '*.pyc' -delete
	rm -rf lib
	rm -f /tmp/nosegae.sqlite3

google_appengine:
	mkdir -p tmp
	wget -O tmp/google_appengine.zip 'https://storage.googleapis.com/appengine-sdks/featured/google_appengine_1.9.40.zip' --no-check-certificate
	unzip tmp/google_appengine.zip
