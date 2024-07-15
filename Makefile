.PHONY: all test clean run-dev deploy deploy_build

all: test

run-dev: loveapp/config.py lib
	dev_appserver.py --dev_appserver_log_level debug dispatch.yaml app.yaml worker.yaml

deploy: deploy_build
	gcloud app deploy app.yaml worker.yaml index.yaml dispatch.yaml --no-promote
	# If you are using cron.yaml uncomment the line below
	# gcloud app deploy cron.yaml

deploy_build: loveapp/config.py clean lib test
	@echo "\033[31mHave you bumped the app version? Hit ENTER to continue, CTRL-C to abort.\033[0m"
	@read ignored

lib: requirements.txt
	mkdir -p lib
	rm -rf lib/*
	pip install -r requirements.txt -t lib

test: 
	pytest tests

clean:
	find . -name '*.pyc' -delete
	rm -rf lib



