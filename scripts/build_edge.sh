#! /usr/bin/env sh

set -e

bash scripts/build_edge-stack.sh
docker-compose -f docker-stack.yml build
