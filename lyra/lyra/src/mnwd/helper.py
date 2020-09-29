import io
import logging
from pathlib import Path
from typing import List, Optional

import pandas
import geopandas
import numpy
import orjson


from lyra.connections import ftp
from lyra.connections import azure_fs
from lyra.connections import database
from lyra.connections.schemas import drop_all_records
from lyra.core.utils import to_categorical_lookup
from lyra.src.mnwd.dt_metrics import dt_metrics
from lyra.src.rsb.graph import rsb_upstream_trace

logger = logging.getLogger(__name__)


def _dt_metrics_slim_tidy(df: pandas.DataFrame, fields: Optional[List[str]] = None):

    # df = pandas.read_csv(file, index_col=0).drop(columns=["date"])
    ix = ["CatchIDN", "Year", "Month"]
    if fields is None:
        fields = [c for c in df.columns if c not in ix]

    df = (
        df.reindex(columns=ix + sorted(fields))
        .melt(id_vars=ix)
        .rename(columns=lambda c: c.lower())
    )
    return df


def get_MNWD_file_obj(slug: str):
    with ftp.mnwd_ftp() as conn:
        file = ftp.get_latest_file_as_object(conn, slug)
    return file


def fetch_and_refresh_drooltool_metrics_file(file=None, share=None):
    if file is None:
        file = get_MNWD_file_obj("drooltool")
    elif isinstance(file, (str, Path)):
        file = open(file, "rb")

    logger.info(f"type: {str(type(file))}")

    if not hasattr(file, "ftp_name"):
        file.ftp_name = "test.csv"

    azure_fs.put_file_object(
        file, "mnwd/drooltool/database/drooltool_latest.csv", share=share
    )
    logger.info(f"{__file__} {file.ftp_name}")

    azure_fs.put_file_object(
        file, f"mnwd/drooltool/database/archive/{file.ftp_name}", share=share
    )
    logger.info(f"{__file__} {file.ftp_name} archived")

    return True


def fetch_and_refresh_oc_rsb_geojson_file(file=None, share=None):
    if file is None:
        file = get_MNWD_file_obj("rsb_geo")

    elif isinstance(file, (str, Path)):
        file = open(file, "rb")

    logger.info(f"type: {str(type(file))}")

    if not hasattr(file, "ftp_name"):
        file.ftp_name = "unnamed.json"

    azure_fs.put_file_object(
        file, "mnwd/drooltool/spatial/rsb_geo_latest.json", share=share
    )
    logger.info(f"{__file__} {file.ftp_name}")

    azure_fs.put_file_object(
        file, f"mnwd/drooltool/spatial/archive/{file.ftp_name}", share=share
    )
    logger.info(f"{__file__} {file.ftp_name} archived")

    # convert to epsg 4326
    file.seek(0)
    gdf = geopandas.read_file(file).to_crs("EPSG:4326")

    file_4326 = io.BytesIO()
    file_4326.write(gdf.to_json().encode())

    azure_fs.put_file_object(
        file_4326, "mnwd/drooltool/spatial/rsb_geo_4326_latest.json", share=share
    )
    logger.info(f"{__file__} rsb_geo_4326_latest")

    # save a slim version for graph traversal and attribute fetching/filtering.
    file_data = io.BytesIO()
    file_data.write(gdf.drop(columns=["geometry"]).to_csv(index=False).encode())

    azure_fs.put_file_object(
        file_data, "mnwd/drooltool/spatial/rsb_geo_data_latest.csv", share=share
    )
    logger.info(f"{__file__} rsb_geo_data_latest")

    return True


def set_drooltool_database_with_file(
    engine, file=None, fields=None, share=None, chunksize=20000
):

    if file is None:
        file = azure_fs.get_file_object(
            "mnwd/drooltool/database/drooltool_latest.csv", share=share
        )

    df = (
        pandas.read_csv(file, index_col=0)
        .drop(columns=["date"], errors="ignore")
        .pipe(_dt_metrics_slim_tidy, fields)
    )

    df, cat = to_categorical_lookup(df, "variable")
    if chunksize is None:
        chunksize = len(df)
    status_list = []
    with engine.begin() as conn:

        drop_all_records("DTMetrics", conn)
        drop_all_records("DTMetricsCategories", conn)
        for k, g in df.groupby(numpy.arange(len(df)) // chunksize):

            _tsql_chunk = int(numpy.floor(2000 / len(g.columns)))
            _msg = (
                f"chunk #{k}; rows {k*chunksize}-{k*chunksize + min(len(g), chunksize)}"
            )

            status1 = database.update_with_log(
                g,
                "DTMetrics",
                conn,
                message=_msg,
                if_exists="append",
                index=False,
                chunksize=_tsql_chunk,
                method="multi",
            )

            # status1=False

            if not status1:
                raise Exception("Error updating DTMetrics database")

            status_list.append(status1)

        status2 = database.update_with_log(
            cat,
            "DTMetricsCategories",
            conn,
            # logconn,
            if_exists="append",
            index=False,
            chunksize=int(numpy.floor(2000 / len(cat.columns))),
            method="multi",
        )
        if not status2:
            raise Exception("Error updating DTMetricsCategories database")

    return all(status_list) & status2


def get_timeseries_from_dt_metrics(
    variable: str,
    site: str,
    start_date: str = None,
    end_date: str = None,
    agg_method: str = "sum",
    trace_upstream: bool = False,
    engine=None,
    **kwargs,
):

    catchidns = [site]
    if trace_upstream:
        catchidns = orjson.loads(rsb_upstream_trace(int(site)))

    result_json = dt_metrics(
        catchidns=catchidns,
        variables=[variable],
        groupby=["variable", "year", "month"],
        agg=agg_method,
        engine=engine,
    )

    df = (
        pandas.read_json(result_json.decode())
        .assign(
            date=lambda df: pandas.to_datetime(
                df["year"].astype(str) + df["month"].astype(str), format="%Y%m"
            )
        )
        .set_index("date")["value"]
    )

    if start_date is not None:
        df = df.loc[start_date:]
    if end_date is not None:
        df = df.loc[:end_date]

    return df
