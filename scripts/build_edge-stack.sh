#! /usr/bin/env sh

set -e

docker-compose \
-f docker-compose.edge.build.yml \
-f docker-compose.shared.depends.yml \
-f docker-compose.shared.env.yml \
-f docker-compose.shared.ports.yml \
-f docker-compose.dev.command.yml \
-f docker-compose.dev.volumes.yml \
config > docker-stack.yml
