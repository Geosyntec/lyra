import logging

import pandas

from lyra.core.config import cfg
from lyra.src.hydstra import api

logger = logging.getLogger(__name__)


def to_hydstra_datetime(date: str, time: str = "") -> str:
    date = date.replace("-", "").ljust(8, "0")
    time = time.replace(":", "").ljust(6, "0")
    return date + time


def hydstra_trace_to_series(trace):
    """trace is a list of dicts from hydstra

    trace = trace_json['return']['traces'][0]['trace']

    trace[0] = {'v': float, 't': "%Y%m%d%H%M%S"}

    """
    df = (
        pandas.DataFrame(trace)
        .assign(date=lambda df: pandas.to_datetime(df["t"], format="%Y%m%d%H%M%S"))
        .assign(value=lambda df: df.v.astype(float))
        .set_index("date")
    )

    return df


async def get_site_variable_as_trace(
    site,
    varfrom,
    varto=None,
    start_date=None,
    end_date=None,
    interval=None,
    agg_method=None,
    datasource=None,
):

    if start_date is None:
        start_date = "0"
    else:
        start_date = to_hydstra_datetime(start_date)

    if end_date is None:
        end_date = "0"
    else:
        end_date = to_hydstra_datetime(end_date)

    if agg_method is None:
        agg_method = "mean"
    if interval is None:
        interval = "hour"
    if varto is None:
        varto = varfrom
    if datasource is None:
        datasource = "PUBLISH"

    trace_json = await api.get_trace(
        site_list=site,
        start_time=start_date,
        end_time=end_date,
        varfrom=varfrom,
        varto=varto,
        interval=interval,
        data_type=agg_method,
        datasource=datasource,
    )

    if len(trace_json.get("return", {}).get("traces", [])):

        return trace_json["return"]["traces"][0]
    else:
        logger.error(trace_json)
        return trace_json
