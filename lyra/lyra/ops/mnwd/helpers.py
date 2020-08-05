from pathlib import Path
import io
import logging
import pandas
import geopandas
import numpy
from typing import List

from lyra.connections.database import update_with_log
from lyra.connections.ftp import mnwd_ftp, get_latest_file_as_object
from lyra.connections.azure_fs import put_file_object, get_file_object
from lyra.core.utils import to_categorical_lookup

logger = logging.getLogger(__name__)


def dt_metrics_to_dataframe(file, fields=None):

    df = pandas.read_csv(file, index_col=0).drop(columns=["date"])
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
    with mnwd_ftp() as conn:
        file = get_latest_file_as_object(conn, slug)
    return file


def fetch_and_refresh_drooltool_metrics_file(file=None, share=None):
    if file is None:
        file = get_MNWD_file_obj("drooltool")
    elif isinstance(file, (str, Path)):
        file = open(file, "rb")

    logger.info(f"type: {str(type(file))}")

    if not hasattr(file, "ftp_name"):
        file.ftp_name = "test.csv"

    put_file_object(file, "mnwd/drooltool/database/drooltool_latest.csv", share=share)
    logger.info(f"{__file__} {file.ftp_name}")

    put_file_object(
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
        file.ftp_name = "test_geo.json"

    put_file_object(file, "mnwd/drooltool/spatial/rsb_geo_latest.json", share=share)
    logger.info(f"{__file__} {file.ftp_name}")

    put_file_object(
        file, f"mnwd/drooltool/spatial/archive/{file.ftp_name}", share=share
    )
    logger.info(f"{__file__} {file.ftp_name} archived")

    # convert to epsg 4326
    file.seek(0)
    gdf = geopandas.read_file(file).to_crs("EPSG:4326")

    file_4326 = io.BytesIO()
    file_4326.write(gdf.to_json().encode())

    put_file_object(
        file_4326, "mnwd/drooltool/spatial/rsb_geo_4326_latest.json", share=share
    )
    logger.info(f"{__file__} rsb_geo_4326_latest")

    return True


def set_drooltool_database_with_file(
    engine, file=None, fields=None, share=None, chunksize=20000
):

    if file is None:
        file = get_file_object(
            "mnwd/drooltool/database/drooltool_latest.csv", share=share
        )

    df = dt_metrics_to_dataframe(file, fields=fields)
    df, cat = to_categorical_lookup(df, "variable")
    status_list = []
    for k, g in df.groupby(numpy.arange(len(df)) // chunksize):

        _tsql_chunk = int(numpy.floor(2000 / len(g.columns)))
        _msg = f"chunk #{k}; rows {k*chunksize}-{k*chunksize + min(len(g), chunksize)}"

        if k == 0:
            if_exists = "replace"
        else:
            if_exists = "append"

        status1 = update_with_log(
            g,
            "DTMetrics",
            engine,
            if_exists=if_exists,
            message=_msg,
            index=False,
            chunksize=_tsql_chunk,
            method="multi",
        )

        status_list.append(status1)

    status2 = update_with_log(
        cat,
        "DTMetricsCategories",
        engine,
        if_exists="replace",
        index=False,
        chunksize=_tsql_chunk,
        method="multi",
    )

    return all(status_list) & status2
