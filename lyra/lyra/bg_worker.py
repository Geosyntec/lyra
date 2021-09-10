import asyncio
import logging

from lyra.connections import database
from lyra.core.cache import flush
from lyra.core.celery_app import celery_app
from lyra.core.config import settings
from lyra.ops import startup
from lyra.src.hydstra.tasks import save_site_geojson_info
from lyra.src.mnwd.tasks import (
    dt_metrics_response,
    rsb_data_response,
    rsb_spatial_response,
    update_drooltool_database,
    update_rsb_geojson,
)
from lyra.src.rsb.tasks import (
    rsb_downstream_trace_response,
    rsb_upstream_trace_response,
)

writer_conn_str = database.sql_server_connection_string(
    user=settings.AZURE_DATABASE_WRITEONLY_USERNAME,
    password=settings.AZURE_DATABASE_WRITEONLY_PASSWORD,
    server=settings.AZURE_DATABASE_SERVER,
    port=settings.AZURE_DATABASE_PORT,
    db=settings.AZURE_DATABASE_NAME,
    driver="ODBC Driver 17 for SQL Server",
    timeout=settings.AZURE_DATABASE_CONNECTION_TIMEOUT,
)

writer_engine = database.database_engine(connection_string=writer_conn_str)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(acks_late=True, track_started=True)
def background_ping():  # pragma: no cover
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
def background_update_drooltool_database(update=True):  # pragma: no cover
    result = update_drooltool_database(engine=writer_engine, update=update)
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_update_rsb_geojson():  # pragma: no cover
    result = update_rsb_geojson()
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_refresh_cache():  # pragma: no cover
    flush()
    startup.prime_cache()
    result = dict(taskname="refresh_cache", succeeded="succeeded")
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_rsb_json_response(**kwargs):  # pragma: no cover
    result = rsb_spatial_response(**kwargs)
    if isinstance(result, bytes):
        return result.decode()
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_rsb_data_response(**kwargs):  # pragma: no cover
    result = rsb_data_response(**kwargs)
    if isinstance(result, bytes):
        return result.decode()
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_dt_metrics_response(**kwargs):  # pragma: no cover
    # try:
    result = dt_metrics_response(**kwargs)
    # except SQLQueryError as e:
    #     result = dict(message=str(e), errors=e.data)
    if isinstance(result, bytes):
        return result.decode()
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_rsb_upstream_trace_response(**kwargs):  # pragma: no cover
    result = rsb_upstream_trace_response(**kwargs)
    if isinstance(result, bytes):
        return result.decode()
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_rsb_downstream_trace_response(**kwargs):  # pragma: no cover
    result = rsb_downstream_trace_response(**kwargs)
    if isinstance(result, bytes):
        return result.decode()
    return result


@celery_app.task(acks_late=True, track_started=True)
def background_update_hydstra_site_info(**kwargs):  # pragma: no cover

    asyncio.run(save_site_geojson_info())
    flush()

    return {"status": "success"}


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
