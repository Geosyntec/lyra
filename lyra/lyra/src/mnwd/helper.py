import io
import logging
from pathlib import Path
from typing import IO, Any, List, Optional, Union

import geopandas
import numpy
import orjson
import pandas
from sqlalchemy.engine import Engine

from lyra.connections import azure_fs, database, ftp
from lyra.connections.schemas import drop_all_records
from lyra.core.errors import SQLQueryError
from lyra.core.utils import to_categorical_lookup
from lyra.src.mnwd.dt_metrics import dt_metrics
from lyra.src.mnwd.spatial import rsb_spatial
from lyra.src.rsb.graph import rsb_upstream_trace

logger = logging.getLogger(__name__)


def _dt_metrics_slim_tidy(
    df: pandas.DataFrame, fields: Optional[List[str]] = None
) -> pandas.DataFrame:

    ix = ["CatchIDN", "Year", "Month"]
    if fields is None:
        fields = [c for c in df.columns if c not in ix]

    df = (
        df.reindex(columns=ix + sorted(fields))
        .melt(id_vars=ix)
        .rename(columns=lambda c: c.lower())
    )
    return df


def get_MNWD_file_obj(slug: str) -> IO[bytes]:
    with ftp.mnwd_ftp() as conn:
        file = ftp.get_latest_file_as_object(conn, slug)
    return file


def fetch_and_refresh_drooltool_metrics_file(
    file: Optional[Union[str, Path, IO[bytes]]] = None,
    share: Optional[azure_fs.ShareClient] = None,
) -> bool:
    if file is None:
        file_obj = get_MNWD_file_obj("drooltool")
    elif isinstance(file, (str, Path)):
        file_obj = open(file, "rb")
        setattr(file_obj, "ftp_name", str(file))
    else:
        file_obj = file

    fname = getattr(file_obj, "ftp_name", "test.json")

    azure_fs.put_file_object(
        file_obj, "swn/mnwd/drooltool/database/drooltool_latest.csv", share=share
    )
    logger.info(f"{__file__} {fname}")

    azure_fs.put_file_object(
        file_obj, f"swn/mnwd/drooltool/database/archive/{fname}", share=share
    )
    logger.info(f"{__file__} {fname} archived")

    return True


def fetch_and_refresh_oc_rsb_geojson_file(
    file: Optional[Union[str, Path, IO[bytes]]] = None,
    share: Optional[azure_fs.ShareClient] = None,
) -> bool:
    if file is None:
        file_obj = get_MNWD_file_obj("rsb_geo")
    elif isinstance(file, (str, Path)):
        file_obj = open(file, "rb")
        setattr(file_obj, "ftp_name", str(file))
    else:
        file_obj = file

    fname = getattr(file_obj, "ftp_name", "test.json")

    azure_fs.put_file_object(
        file_obj, "swn/mnwd/drooltool/spatial/rsb_geo_latest.json", share=share
    )
    logger.info(f"{__file__} {fname}")

    azure_fs.put_file_object(
        file_obj, f"swn/mnwd/drooltool/spatial/archive/{fname}", share=share
    )
    logger.info(f"{__file__} {fname} archived")

    # convert to epsg 4326
    file_obj.seek(0)
    gdf = geopandas.read_file(file_obj).to_crs("EPSG:4326")

    file_4326 = io.BytesIO()
    file_4326.write(gdf.to_json().encode())

    azure_fs.put_file_object(
        file_4326, "swn/mnwd/drooltool/spatial/rsb_geo_4326_latest.json", share=share
    )
    logger.info(f"{__file__} rsb_geo_4326_latest")

    topojson_file = io.BytesIO()
    topojson_file.write(rsb_spatial())

    azure_fs.put_file_object(
        topojson_file,
        "swn/mnwd/drooltool/spatial/rsb_topo_4326_latest.json",
        share=share,
    )
    logger.info(f"{__file__} rsb_topo_4326_latest")

    # save a slim version for graph traversal and attribute fetching/filtering.
    file_data = io.BytesIO()
    data = (
        gdf.assign(rep_pt=lambda df: df.geometry.representative_point())
        .assign(rep_x=lambda df: df["rep_pt"].x)
        .assign(rep_y=lambda df: df["rep_pt"].y)
        .drop(columns=["geometry", "rep_pt"])
    )
    file_data.write(data.to_csv(index=False).encode())

    azure_fs.put_file_object(
        file_data, "swn/mnwd/drooltool/spatial/rsb_geo_data_latest.csv", share=share
    )
    logger.info(f"{__file__} rsb_geo_data_latest")

    return True


def set_drooltool_database_with_file(
    engine: Engine,
    file: Optional[Union[str, Path, IO[bytes]]] = None,
    fields: Optional[List[str]] = None,
    share: Optional[azure_fs.ShareClient] = None,
    chunksize: Optional[int] = 20000,
) -> bool:

    if file is None:
        file_obj = azure_fs.get_file_object(
            "swn/mnwd/drooltool/database/drooltool_latest.csv", share=share
        )
    elif isinstance(file, (str, Path)):
        file_obj = open(file, "rb")
    else:
        file_obj = file

    df = (
        pandas.read_csv(file_obj, index_col=0)
        .drop(columns=["date"], errors="ignore")
        .pipe(_dt_metrics_slim_tidy, fields)
    )

    df, cat = to_categorical_lookup(df, "variable")
    if chunksize is None:
        chunksize = len(df)
    status_list: List[bool] = []

    database.reconnect_engine(engine)
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

        status2: bool = database.update_with_log(
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
    start_date: str,
    end_date: str,
    agg_method: str = "sum",
    trace_upstream: bool = False,
    engine: Optional[Engine] = None,
    interval: Optional[str] = "month",
    **kwargs: Any,
) -> pandas.DataFrame:

    catchidns = [site]
    if trace_upstream:
        catchidns = orjson.loads(rsb_upstream_trace(int(site)))

    if interval == "year":
        groupby = ["variable", "year"]
    else:
        groupby = ["variable", "year", "month"]

    try:

        result_json = dt_metrics(
            catchidns=catchidns,
            variables=[variable],
            groupby=groupby,
            agg=agg_method,
            engine=engine,
        )

        df = pandas.read_json(result_json.decode())

        if interval == "year":

            df = df.assign(
                date=lambda df: pandas.to_datetime(df["year"].astype(str), format="%Y")
            ).set_index("date")["value"]

        else:
            df = df.assign(
                date=lambda df: pandas.to_datetime(
                    df["year"].astype(str) + df["month"].astype(str), format="%Y%m"
                )
            ).set_index("date")["value"]

        if start_date is not None:
            df = df.loc[start_date:]  # type: ignore
        if end_date is not None:
            df = df.loc[:end_date]  # type: ignore

    except SQLQueryError:  # this is raised when the query returned is empty.
        freq = "MS"
        if interval == "year":
            freq = "YS"
        index = pandas.date_range(
            name="date", start=start_date, end=end_date, freq=freq
        )

        df = pandas.Series(0, index=index, name="value")

    return df.to_frame()
