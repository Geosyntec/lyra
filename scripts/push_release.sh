#! /usr/bin/env sh

set -e

tag=$(grep __version__ ./lyra/lyra/__init__.py | cut -d '=' -f2 | sed 's/"//g' | tr -d '[:space:]')

echo "building tagged release: $tag"
bash scripts/build_prod.sh -t "$tag"
docker-compose -f docker-stack${tag}.yml push

echo "building UNtagged release (latest)"
bash scripts/build_prod.sh
docker-compose -f docker-stack.yml push
