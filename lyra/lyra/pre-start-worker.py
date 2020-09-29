import logging

from lyra.core.config import settings
from lyra.connections.database import engine, reconnect_engine
from lyra.ops import startup


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:

    reconnect_engine(engine)
    logger.info(f"engine: {engine.url}\ntables: {engine.table_names()}")

    if not settings.FORCE_FOREGROUND:
        startup.get_redis_connection()


def main() -> None:
    logger.info("Initializing service")
    init()
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
