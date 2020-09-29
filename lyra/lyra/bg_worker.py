import time
import logging

from lyra.core.celery_app import celery_app
from lyra.core.cache import flush
from lyra.core.errors import SQLQueryError

from lyra.ops import startup

# from lyra.tasks import build_static_references

from lyra.src.mnwd.tasks import (
    update_drooltool_database,
    update_rsb_geojson,
    rsb_spatial_response,
    rsb_data_response,
    dt_metrics_response,
)

from lyra.src.rsb.tasks import (
    rsb_upstream_trace_response,
    rsb_downstream_trace_response,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(acks_late=True, track_started=True)
def background_ping():
    logger.info("background pinged")
    return True


## This task has no effect when run on dev or on prod; only local v0.1.16
# @celery_app.task(acks_late=True, track_started=True)
# def background_build_static_references():
#     succeeded = build_static_references.main()
#     result = dict(taskname="build_static_references", succeeded=succeeded)
#     flush()
#     return result


@celery_app.task(acks_late=True, track_started=True)
def background_update_drooltool_database(update=True):
    result = update_drooltool_database(update=update)
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_update_rsb_geojson():
    result = update_rsb_geojson()
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_refresh_cache():
    flush()
    startup.prime_cache()
    result = dict(taskname="refresh_cache", succeeded="succeeded")
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_rsb_json_response(**kwargs):
    result = rsb_spatial_response(**kwargs)
    if isinstance(result, bytes):
        return result.decode()
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_rsb_data_response(**kwargs):
    result = rsb_data_response(**kwargs)
    if isinstance(result, bytes):
        return result.decode()
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_dt_metrics_response(**kwargs):
    # try:
    result = dt_metrics_response(**kwargs)
    # except SQLQueryError as e:
    #     result = dict(message=str(e), errors=e.data)
    if isinstance(result, bytes):
        return result.decode()
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_rsb_upstream_trace_response(**kwargs):
    result = rsb_upstream_trace_response(**kwargs)
    if isinstance(result, bytes):
        return result.decode()
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_rsb_downstream_trace_response(**kwargs):
    result = rsb_downstream_trace_response(**kwargs)
    if isinstance(result, bytes):
        return result.decode()
    return result


# # -------------------- Nothing -----------------
# def sleep_task(duration):
#     logger.debug(f"sleeping for {duration} seconds.")
#     time.sleep(duration)
#     logger.debug("done sleeping")
#     result = {"process": {"name": "sleeping", "duration_seconds": duration}}
#     result["processor"] = "celery_task"
#     return result


# # @cache_decorator
# def cached_sleep_task(duration):
#     return sleep_task(duration)


# @celery_app.task(acks_late=True, track_started=True)
# def background_run_sleep_in_background(duration):
#     result = sleep_task(duration)
#     return result  # pragma: no cover


# @celery_app.task(acks_late=True, track_started=True)
# def background_run_sleep_in_background_cached(duration):
#     result = cached_sleep_task(duration)
#     return result  # pragma: no cover


# @celery_app.task(acks_late=True, track_started=True)
# def add(a, b):
#     return a + b
