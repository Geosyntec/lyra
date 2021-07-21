#! /usr/bin/env sh

set -e
set -x

black . --check
isort . --check --diff
mkdir -p .mypy_cache
mypy lyra/lyra --install-types --non-interactive
