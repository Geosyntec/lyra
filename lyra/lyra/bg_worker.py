import time
import logging

from lyra.core.celery_app import celery_app
from lyra.core.cache import cache_decorator, flush
from lyra.tasks import build_static_references

from lyra.ops.mnwd.tasks import update_drooltool_database, update_rsb_geojson, rsb_json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(acks_late=True, track_started=True)
def background_build_static_references():
    build_static_references.main()
    flush()
    return True


@celery_app.task(acks_late=True, track_started=True)
def background_update_drooltool_database(update=True):
    result = update_drooltool_database(update=update)
    flush()
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_update_rsb_geojson():
    result = update_rsb_geojson()
    flush()
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_rsb_json(
    f: str = "topojson", xmin=None, ymin=None, xmax=None, ymax=None, **kwargs
):
    result = rsb_json(f=f, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, **kwargs)
    return result


# -------------------- Nothing -----------------
def sleep_task(duration):
    logger.debug(f"sleeping for {duration} seconds.")
    time.sleep(duration)
    logger.debug("done sleeping")
    result = {"process": {"name": "sleeping", "duration_seconds": duration}}
    result["processor"] = "celery_task"
    return result


# @cache_decorator
def cached_sleep_task(duration):
    return sleep_task(duration)


@celery_app.task(acks_late=True, track_started=True)
def background_run_sleep_in_background(duration):
    result = sleep_task(duration)
    return result  # pragma: no cover


@celery_app.task(acks_late=True, track_started=True)
def background_run_sleep_in_background_cached(duration):
    result = cached_sleep_task(duration)
    return result  # pragma: no cover


@celery_app.task(acks_late=True, track_started=True)
def add(a, b):
    return a + b
