#! /usr/bin/env sh

set -e
REG=$(grep __version__ ./lyra/lyra/__init__.py | cut -d '=' -f2 | sed 's/"//g' | tr -d '[:space:]')
echo "$REG" > VERSION
