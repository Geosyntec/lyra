import logging
from datetime import datetime

import pandas
import sqlalchemy
from sqlalchemy import create_engine
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from lyra.core.config import settings

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(60 * 5),  # 5 mins
    wait=wait_fixed(2),  # 2 seconds
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def reconnect_engine(engine):
    try:
        with engine.begin() as conn:
            # this should connect/login and ensure that the database is available.
            conn.execute("select 1").fetchall()

    except Exception as e:
        logger.error(e)
        raise e


def sql_server_connection_string(
    user: str,
    password: str,
    server: str,
    port: str,
    db: str,
    driver: str = "ODBC Driver 17 for SQL Server",
    timeout: int = 15,
) -> str:  # pragma: no cover
    return f"mssql+pyodbc://{user}:{password}@{server}:{port}/{db}?driver={driver};connect_timeout={timeout};"


def sqlite_connection_string(filepath: str = "") -> str:  # pragma: no cover
    return "sqlite:///" + filepath


def get_connection_string(settings=settings):
    if not settings.AZURE_DATABASE_SERVER:  # pragma: no cover
        conn_str = sqlite_connection_string()
    else:
        conn_str = sql_server_connection_string(
            user=settings.AZURE_DATABASE_USERNAME,
            password=settings.AZURE_DATABASE_PASSWORD,
            server=settings.AZURE_DATABASE_SERVER,
            port=settings.AZURE_DATABASE_PORT,
            db=settings.AZURE_DATABASE_NAME,
            driver="ODBC Driver 17 for SQL Server",
            timeout=settings.AZURE_DATABASE_CONNECTION_TIMEOUT,
        )
        # conn_str = sqlalchemy.engine.url.URL(
        #     drivername="mssql+pyodbc",
        #     username=settings.AZURE_DATABASE_USERNAME,
        #     password=settings.AZURE_DATABASE_PASSWORD,
        #     host=settings.AZURE_DATABASE_SERVER,
        #     port=settings.AZURE_DATABASE_PORT,
        #     database=settings.AZURE_DATABASE_NAME,
        #     query={
        #         "driver": "ODBC Driver 17 for SQL Server",
        #         "connect_timeout": settings.AZURE_DATABASE_CONNECTION_TIMEOUT,
        #     },
        # )
    return conn_str


def database_engine(connection_string=None, settings=settings):
    if connection_string is None:  # pragma: no branch
        connection_string = get_connection_string(settings)
    return create_engine(connection_string, pool_pre_ping=True)


def update_with_log(df, table, conn, message="", **kwargs):

    record = dict(status="success", table_name=table, date_initiated=datetime.utcnow(),)

    try:
        # with engine.begin() as conn:
        df.to_sql(table, conn, **kwargs)
        record["date_completed"] = datetime.utcnow()
        logger.info("database operation was successful")
        record["message"] = message

    except Exception as e:  # pragma: no cover
        record["status"] = "failure"
        record["message"] = str(e)
        logger.error("database operation failed")
        logger.error(str(e))

    finally:
        try:
            status_record = pandas.DataFrame([record])
            # with engine.begin() as conn:
            status_record.to_sql(
                "TableChangeLog", conn, if_exists="append", index=False
            )
            logger.info("database operation logged")
        except Exception as e:  # pragma: no cover
            logger.error(str(e))
            return False

    if record["status"] == "failure":  # pragma: no cover
        return False

    return True


engine = database_engine()  # each bg task will have its own engine
