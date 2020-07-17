import time
import logging

from lyra.core.celery_app import celery_app
from lyra.core.cache import cache_decorator
from lyra.tasks import build_static_references

logger = logging.getLogger(__name__)


@celery_app.task(acks_late=True, track_started=True)
def background_build_static_references():
    build_static_references.main()
    return True


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
