from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.engine import Engine

from lyra.connections.azure_fs import ShareClient
from lyra.connections.database import engine, reconnect_engine
from lyra.core.cache import cache_decorator
from lyra.core.config import config
from lyra.src.mnwd import dt_metrics, spatial
from lyra.src.mnwd.helper import (
    fetch_and_refresh_drooltool_metrics_file,
    fetch_and_refresh_oc_rsb_geojson_file,
    set_drooltool_database_with_file,
)

## Scheduled jobs and updates
## --------------------------


def update_drooltool_database(
    engine: Engine = engine,
    update: bool = True,
    file: Optional[Union[str, Path]] = None,
    fields_from_config: bool = True,
    share: Optional[ShareClient] = None,
) -> Dict:

    if update:
        fetch_and_refresh_drooltool_metrics_file(file=file, share=share)

    cfg = config()

    fields = None
    if fields_from_config:
        fields = [dct["variable"] for dct in cfg["mnwd"]["dt_metrics"]["fields"]]
        # metrics = list(
        #     filter(
        #         lambda x: cfg["variables"][x]["source"] == "dt_metrics",
        #         cfg["variables"],
        #     )
        # )
        # fields = [cfg["variables"][m]['varfrom'] for m in metrics]

    reconnect_engine(engine)  # may have to reconnect and login to wake from sleep.

    response = dict(
        taskname="update_drooltool_database",
        succeeded=set_drooltool_database_with_file(
            engine, file=file, fields=fields, share=share
        ),
    )

    return response


def update_rsb_geojson(
    file: Optional[Union[str, Path]] = None, share: Optional[ShareClient] = None,
) -> Dict:
    succeeded = fetch_and_refresh_oc_rsb_geojson_file(file=file, share=share)
    response = dict(taskname="update_rsb_geojson", succeeded=succeeded)

    return response


## route tasks
## -----------


@cache_decorator(ex=3600 * 6, as_response=True)  # expires in 6 hours
def rsb_spatial_response(**kwargs: Any) -> bytes:
    result: bytes = spatial.rsb_spatial(**kwargs)
    return result


@cache_decorator(ex=3600 * 6, as_response=True)  # expires in 6 hours
def rsb_data_response(**kwargs: Any) -> bytes:
    result: bytes = spatial._rsb_data_bytestring(**kwargs)
    return result


@cache_decorator(ex=3600 * 6, as_response=True)  # expires in 6 hours
def dt_metrics_response(
    catchidns: Optional[List[int]] = None,
    variables: Optional[List[str]] = None,
    years: Optional[List[int]] = None,
    months: Optional[List[int]] = None,
    groupby: Optional[List[str]] = None,
    agg: Optional[str] = None,
) -> bytes:
    result: bytes = dt_metrics.dt_metrics(
        catchidns=catchidns,
        variables=variables,
        years=years,
        months=months,
        groupby=groupby,
        agg=agg,
    )
    return result
