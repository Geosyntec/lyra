#! /usr/bin/env sh

set -e
set -x

black . --check
isort . --check --diff --profile black
# mypy lyra/lyra
