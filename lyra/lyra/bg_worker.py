import asyncio
import logging

from lyra.connections.database import writer_engine
from lyra.core.cache import flush
from lyra.core.celery_app import celery_app
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(acks_late=True, track_started=True)
def background_ping():  # pragma: no cover
    logger.info("background pinged")
    return True


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
    result = dt_metrics_response(**kwargs)
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
