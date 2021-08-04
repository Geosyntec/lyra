import asyncio
from typing import Any, Dict, List, Optional, Union

from lyra.core import async_requests
from lyra.core.config import settings
from lyra.models import hydstra_models


async def get_site_list():
    site_list = {
        "function": "get_site_list",
        "version": 1,
        "params": {"site_list": "TABLE(SITE)"},
    }

    return await async_requests.send_request(
        settings.HYDSTRA_BASE_URL, payload=site_list
    )


async def get_swn_site_list() -> Dict[str, Any]:
    site_list = {
        "function": "get_site_list",
        "version": 1,
        "params": {"site_list": "GROUP(SITE_TYPE,SWN_ALISO)"},
    }

    return await async_requests.send_request(
        settings.HYDSTRA_BASE_URL, payload=site_list
    )


async def get_sites_db_info(
    site: Optional[str] = None,
    field_list: Optional[List[str]] = None,
    return_type: Optional[hydstra_models.ReturnType] = None,
    filter_values: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    if filter_values is None:  # pragma: no branch
        filter_values = {}

    get_db_info: Dict = {
        "function": "get_db_info",
        "version": "3",
        "params": {
            "table_name": "site",
            "return_type": getattr(
                hydstra_models.ReturnType,
                str(return_type),
                hydstra_models.ReturnType.array,
            ),
            "filter_values": filter_values,
        },
    }
    if site is not None:
        get_db_info["params"]["filter_values"]["station"] = site

    if field_list is not None:  # pragma: no cover
        get_db_info["params"]["field_list"] = field_list  # pass as array

    return await async_requests.send_request(
        settings.HYDSTRA_BASE_URL, payload=get_db_info
    )


async def get_site_db_info(
    site: str,
    return_type: Optional[hydstra_models.ReturnType] = None,
    field_list: Optional[List[str]] = None,
) -> Dict[str, Any]:

    get_db_info: Dict = {
        "function": "get_db_info",
        "version": "3",
        "params": {
            "table_name": "site",
            "return_type": getattr(
                hydstra_models.ReturnType,
                str(return_type),
                hydstra_models.ReturnType.array,
            ),
            "filter_values": {"station": site},
        },
    }

    if field_list is not None:  # pragma: no cover
        get_db_info["params"]["field_list"] = field_list  # pass as array

    return await async_requests.send_request(
        settings.HYDSTRA_BASE_URL, payload=get_db_info
    )


async def get_site_geojson(
    site_list: Optional[List[str]] = None,
    field_list: Optional[List[str]] = None,
    get_elev: Optional[int] = 0,
) -> Dict[str, Any]:

    if site_list is None:
        site_list_response = await get_site_list()
        site_list = site_list_response["return"]["sites"]

    if field_list is None:
        field_list = [
            "station",
            "latitude",
            "longitude",
            "stntype",
            "stname",
            "shortname",
        ]

    get_site_geojson_payload = {
        "function": "get_site_geojson",
        "version": 2,
        "params": {
            "site_list": ",".join(site_list),
            "get_elev": get_elev,
            "fields": field_list,
        },
    }

    return await async_requests.send_request(
        settings.HYDSTRA_BASE_URL, payload=get_site_geojson_payload
    )


async def get_trace(
    site_list: List[str],
    start_time: str,
    interval: hydstra_models.Interval,
    datasource: str,
    end_time: str,
    data_type: hydstra_models.DataType,
    interval_multiplier: int = 1,
    recent_points: Optional[int] = None,
    var_list: Optional[Union[str, List[str]]] = None,
    varto: Optional[str] = None,
    varfrom: Optional[str] = None,
    **kwargs: Optional[Dict[str, Any]],
) -> Dict[str, Any]:

    ts_trace: Dict = {
        "function": "get_ts_traces",
        "version": 2,
        "params": {
            "site_list": ",".join(site_list),
            "start_time": start_time,
            "interval": getattr(hydstra_models.Interval, interval),
            "datasource": datasource,
            "end_time": end_time,
            "data_type": getattr(hydstra_models.DataType, data_type),
            "recent_points": recent_points,
            "rounding": [
                {
                    "zero_no_dec": "1",
                    "dec_first": "1",
                    "sigfigs": "6",
                    "variable": "100",
                }
            ],
            "multiplier": interval_multiplier,
        },
    }

    if var_list is not None:
        if isinstance(var_list, list):
            var_list = ",".join(var_list)
        ts_trace["params"]["var_list"] = var_list
    else:
        ts_trace["params"]["varfrom"] = varfrom
        ts_trace["params"]["varto"] = varto or varfrom

    return await async_requests.send_request(
        settings.HYDSTRA_BASE_URL, payload=ts_trace
    )


async def get_datasources(
    site_list: Optional[List[str]] = None, ts_classes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if site_list is None:
        site_list_response = await get_site_list()
        site_list = site_list_response["return"]["sites"]

    get_datasources_by_site: Dict = {
        "function": "get_datasources_by_site",
        "version": 1,
        "params": {"site_list": ",".join(site_list),},
    }

    if ts_classes is not None:
        get_datasources_by_site["params"]["ts_classes"] = ",".join(ts_classes)

    return await async_requests.send_request(
        settings.HYDSTRA_BASE_URL, payload=get_datasources_by_site
    )


async def get_variables(
    site_list: Optional[List[str]] = None,
    datasource: str = "PUBLISH",
    var_filter: Optional[List[str]] = None,
) -> Dict[str, Any]:

    if site_list is None:
        site_list_response = await get_site_list()
        site_list = site_list_response["return"]["sites"]

    get_variable_list = {
        "function": "get_variable_list",
        "version": 1,
        "params": {
            "site_list": None if not site_list else ",".join(site_list),
            "datasource": datasource,
            "var_filter": None if not var_filter else ",".join(var_filter),
        },
    }

    return await async_requests.send_request(
        settings.HYDSTRA_BASE_URL, payload=get_variable_list
    )


async def get_site_variables(
    site: str, variable: Optional[str] = None, datasource: str = "PUBLISH",
) -> Dict[str, Any]:

    get_variable_list = {
        "function": "get_variable_list",
        "version": 1,
        "params": {
            "site_list": site,
            "datasource": datasource,
            "var_filter": variable,
        },
    }

    return await async_requests.send_request(
        settings.HYDSTRA_BASE_URL, payload=get_variable_list
    )


async def get_variables_db_info(
    return_type: Optional[hydstra_models.ReturnType] = None,
    filter_values: Optional[Dict] = None,
) -> Dict[str, Any]:

    if filter_values is None:
        filter_values = {}

    get_db_info = {
        "function": "get_db_info",
        "version": "3",
        "params": {
            "table_name": "variable",
            "return_type": getattr(
                hydstra_models.ReturnType,
                str(return_type),
                hydstra_models.ReturnType.array,
            ),
            "filter_values": filter_values,
        },
    }

    return await async_requests.send_request(
        settings.HYDSTRA_BASE_URL, payload=get_db_info
    )
