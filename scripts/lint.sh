#! /usr/bin/env sh

set -e
set -x

ruff check ./lyra/lyra --diff
ruff format ./lyra/lyra --diff
