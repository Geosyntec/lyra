import logging

import pandas
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed
from azure.core.exceptions import ResourceNotFoundError

import lyra.bg_worker as bg
from lyra.core.cache import redis_cache
from lyra.connections.schemas import init_all
from lyra.connections.azure_fs import get_share
from lyra.src.mnwd.tasks import update_drooltool_database
from lyra.src.mnwd.dt_metrics import dt_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


max_tries = 30 * 5  # 5 minutes
wait_seconds = 2


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init_schemas(engine):
    try:
        init_all(engine)
    except Exception as e:
        logger.error(e)
        raise e


def startup_mnwd_drooltool_metrics_database(engine):

    tables = engine.table_names()
    db_exists = all(t in tables for t in ["DTMetrics", "DTMetricsCategories"])

    if db_exists:

        with engine.begin() as conn:
            df = pandas.read_sql("select top 1 * from DTMetrics", con=conn)
        if len(df) > 0:
            logger.info("DTMetrics table exists and has data")
            logger.info("... exiting drool tool metrics startup")
            return

    share = get_share()
    fc = share.get_file_client("mnwd/drooltool/database/drooltool_latest.csv")

    try:
        fc.get_file_properties()
        update = False
        logger.info("DT file exists")
    except ResourceNotFoundError:
        update = True
        logger.info("downloading DT file from MNWD FTP")

    logger.info("initializing DTMetrics database table")
    update_drooltool_database(
        engine=engine, file=None, update=update,
    )


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def get_redis_connection():  # TODO
    try:
        assert redis_cache.ping()
    except Exception as e:
        logger.error(e)
        raise e


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def get_background_worker_connection():
    try:
        bg.background_ping.apply_async().get(timeout=0.2)
    except Exception as e:
        logger.error(e)
        raise e


def prime_cache():
    bg.background_rsb_json_response.apply_async()
    bg.background_rsb_data_response.apply_async()
    bg.background_dt_metrics_response.apply_async()
    bg.background_rsb_upstream_trace_response.apply_async(kwargs=dict(catchidn=0))
