MAKEFLAGS += --silent
.PHONY: clean clean-test clean-pyc clean-build restart test develop up down dev-server help build release
.DEFAULT_GOAL := help
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -fr .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache
	rm -fr .mypy_cache

export COMPOSE_DOCKER_CLI_BUILD=1

build: ## build the docker-stack.yml file
	docker-compose -f docker-stack.yml build

restart: ## restart the redis server and the background workers
	docker-compose -f docker-stack.yml restart redis celeryworker

test: clean ## run tests quickly with the default Python
	bash scripts/test.sh -xsv

coverage: clean restart ## check code coverage quickly with the default Python
	docker-compose -f docker-stack.yml exec lyra-tests coverage run -m pytest -x
	docker-compose -f docker-stack.yml exec lyra-tests coverage report -mi

typecheck: clean ## run static type checker
	mypy lyra/lyra

develop: clean ## build the development environment and launch containers in background
	bash scripts/build_dev.sh
	
up: ## bring up the containers in '-d' mode 
	docker-compose -f docker-stack.yml up -d

down: ## bring down the containers and detach volumes
	docker-compose -f docker-stack.yml down -v

dev-server: ## start a development server
	docker-compose -f docker-stack.yml run -p 8080:80 -e LOG_LEVEL=debug lyra bash /start-reload.sh

release: ## push production images to registry
	bash scripts/push_release.sh
