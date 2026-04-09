#! /usr/bin/env sh

# coverage run --source=lyra/lyra/src --branch -m 
pytest lyra/lyra/tests/test_src -xsv -k "not integration"
# coverage report -mi --omit=*test*