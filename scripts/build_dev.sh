#! /usr/bin/env sh

set -e
export COMPOSE_FILE=docker-stack.yml
export COMPOSE_DOCKER_CLI_BUILD=1

bash scripts/build_dev-stack.sh
docker-compose -f docker-stack.yml build
