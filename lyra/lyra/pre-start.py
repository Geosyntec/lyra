import logging
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

import pandas

from lyra.core.config import settings
from lyra.core.cache import redis_cache
from lyra.connections.database import engine
from lyra.connections.schemas import init_all

from lyra.ops.mnwd.tasks import update_drooltool_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


max_tries = 60 * 5  # 5 minutes
wait_seconds = 2


def startup_mnwd_drooltool_metrics_database(engine):

    db_exists = "DTMetrics" in engine.table_names()

    if db_exists:

        with engine.begin() as conn:
            df = pandas.read_sql("select top 1 * from DTMetrics", con=conn)
        if len(df) > 0:
            logger.info("DTMetrics table exists and has data")
            logger.info("... exiting drool tool metrics startup")
            return

    logger.info("initializing DTMetrics table")
    update_drooltool_database(
        engine=engine, file=None, update=False,
    )


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init() -> None:
    try:
        init_all(engine)
    except Exception as e:
        logger.error(e)
        raise e

    logger.info(f"engine: {engine.url}\ntables: {engine.table_names()}")

    try:
        startup_mnwd_drooltool_metrics_database(engine)
    except Exception as e:
        logger.error(e)
        raise e

    if not settings.FORCE_FOREGROUND:
        try:
            assert redis_cache.ping()
        except Exception as e:
            logger.error()
            raise e


def main() -> None:
    logger.info("Initializing service")
    init()
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
