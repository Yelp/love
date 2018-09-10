.PHONY: all test clean run-dev deploy deploy_build

all: test

run-dev: config.py lib
	dev_appserver.py --enable_console true --dev_appserver_log_level debug dispatch.yaml app.yaml worker.yaml

deploy: deploy_build
	# If you are running into permission issues and see a message like this:
	# You do not have permission to modify this app (app_id=u'foobar').
	# then try adding --no_cookies to the commands below
	appcfg.py update app.yaml worker.yaml
	appcfg.py update_dispatch .
	appcfg.py update_queues .
	appcfg.py update_indexes .
	# If you are using cron.yaml uncomment the line below
	# appcfg.py update_cron .

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
