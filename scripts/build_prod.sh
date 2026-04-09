#! /usr/bin/env sh

set -e
export COMPOSE_FILE=docker-stack.yml
export COMPOSE_DOCKER_CLI_BUILD=1

while getopts t: flag
do
    case "${flag}" in
        t) tag=${OPTARG};;
    esac
done

bash scripts/build_prod-stack.sh -t "$tag"
docker-compose -f docker-stack${tag}.yml build
