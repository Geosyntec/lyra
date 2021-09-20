import logging

from lyra.connections.database import writer_engine, reconnect_engine
from lyra.core.config import settings
from lyra.ops import startup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:

    reconnect_engine(writer_engine)
    logger.info(f"engine: {writer_engine.url}\ntables: {writer_engine.table_names()}")
    startup.init_schemas(writer_engine)
    startup.startup_mnwd_drooltool_metrics_database(writer_engine)

    if not settings.FORCE_FOREGROUND:
        startup.get_redis_connection()
        startup.get_background_worker_connection()
        startup.prime_cache()
    else:
        logger.info("FORCE_FOREGROUND is set; background worker disabled.")


def main() -> None:
    logger.info("Initializing service")
    init()
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
