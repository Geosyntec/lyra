from datetime import datetime
import logging

import pandas
from sqlalchemy import create_engine

from lyra.core.config import settings

logger = logging.getLogger(__name__)


def sql_server_connection_string(
    user: str, password: str, server: str, port: str, db: str, driver: str, timeout: int
) -> str:
    return f"mssql+pyodbc://{user}:{password}@{server}:{port}/{db}?driver={driver};connect_timeout={timeout}"


def sqlite_connection_string(filepath: str = "") -> str:
    return "sqlite:///" + filepath


def get_connection_string(settings=settings):
    if not settings.AZURE_DATABASE_SERVER:
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
    return conn_str


def database_engine(connection_string=None, settings=settings):
    if connection_string is None:
        connection_string = get_connection_string(settings)
    return create_engine(connection_string, pool_pre_ping=True,)


def update_with_log(df, table, engine, message="", **kwargs):
    record = dict(status="success", table_name=table, date_initiated=datetime.utcnow(),)

    try:
        with engine.begin() as conn:
            df.to_sql(table, conn, **kwargs)
            record["date_completed"] = datetime.utcnow()
            logger.info("database operation was successful")
            record["message"] = message

    except Exception as e:
        record["status"] = "failure"
        record["message"] = str(e)
        logger.info("database operation failed")

    finally:
        try:
            status_record = pandas.DataFrame([record])
            with engine.begin() as conn:
                status_record.to_sql(
                    "TableChangeLog", conn, if_exists="append", index=False
                )
                logger.info("database operation logged")
        except Exception as e:
            logger.error(str(e))  # or log it!
            return False

    if record["status"] == "failure":
        return False

    return True


engine = database_engine()  # each bg task will have its own engine
