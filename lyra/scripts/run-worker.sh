#! /usr/bin/env sh

# ref: https://github.com/tiangolo/uvicorn-gunicorn-docker/blob/master/python3.6/start.sh

set -e

# If there's a prestart.sh script in the /lyra directory, run it before starting
PRE_START_PATH=/lyra/lyra/prestart-worker.sh
echo "Checking for script in $PRE_START_PATH"
if [ -f $PRE_START_PATH ] ; then
    echo "Running script $PRE_START_PATH"
    . "$PRE_START_PATH"
else
    echo "There is no script $PRE_START_PATH"
fi
celery --app lyra.bg_worker worker -l INFO -c 4 -O fair -B
