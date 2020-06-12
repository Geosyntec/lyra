from typing import Any, Dict, List, Optional, Union

# import requests
import orjson
import aiohttp
import pandas

# from celery.result import AsyncResult
from fastapi import APIRouter, Body, Query
from fastapi.requests import Request
from fastapi.responses import ORJSONResponse
from fastapi.templating import Jinja2Templates

from pydantic import Field

from lyra.api.models import hydstra_models
from lyra.core import config
from lyra.core.async_requests import send_request


router = APIRouter()


@router.get(
    "/sites", response_class=ORJSONResponse,
)
async def get_site_list():
    get_site_list = {
        "function": "get_site_list",
        "version": 1,
        "params": {"site_list": "TSFILES(DSOURCES(tscARCHIVE))"},
    }

    return await send_request(config.HYDSTRA_BASE_URL, payload=get_site_list)


@router.get(
    "/sites/info", response_class=ORJSONResponse,
)
@router.post(
    "/sites/info", response_class=ORJSONResponse,
)
async def get_sites_db_info(
    site: Optional[str] = Query(None, example="TRABUCO"),
    field_list: Optional[List[str]] = Query(None),
    return_type: Optional[hydstra_models.ReturnType] = "array",
    filter_values: Optional[Dict] = Body({}, example={"active": True}),
):
    get_db_info = {
        "function": "get_db_info",
        "version": "3",
        "params": {
            "table_name": "site",
            "return_type": return_type,
            "filter_values": filter_values,
        },
    }
    if site is not None:
        get_db_info["params"]["filter_values"]["station"] = site

    if field_list is not None:
        get_db_info["params"]["field_list"] = field_list  # pass as array

    return await send_request(config.HYDSTRA_BASE_URL, payload=get_db_info)


@router.get(
    "/sites/{site}/info", response_class=ORJSONResponse,
)
async def get_site_db_info(
    site: str,
    return_type: Optional[hydstra_models.ReturnType] = "array",
    field_list: Optional[List[str]] = Query(None),
):
    get_db_info = {
        "function": "get_db_info",
        "version": "3",
        "params": {
            "table_name": "site",
            "return_type": return_type,
            "filter_values": {"station": site},
        },
    }

    if field_list is not None:
        get_db_info["params"]["field_list"] = field_list  # pass as array

    return await send_request(config.HYDSTRA_BASE_URL, payload=get_db_info)


@router.get(
    "/sites/spatial", response_class=ORJSONResponse,
)
async def get_site_geojson(
    site_list: Optional[List[str]] = Query(None),
    field_list: Optional[List[str]] = Query(
        None,
        example=["station", "latitude", "longitude", "stntype", "stname", "shortname",],
    ),
    get_elev: Optional[int] = 0,
):

    if site_list is None:
        site_list_response = await get_site_list()
        site_list = site_list_response["_return"]["sites"]

    if field_list is None:
        field_list = [
            "station",
            "latitude",
            "longitude",
            "stntype",
            "stname",
            "shortname",
        ]

    get_site_geojson = {
        "function": "get_site_geojson",
        "version": 2,
        "params": {
            "site_list": ",".join(site_list),
            "get_elev": get_elev,
            "fields": field_list,
        },
    }

    return await send_request(config.HYDSTRA_BASE_URL, payload=get_site_geojson)


@router.get(
    "/sites/datasources", response_class=ORJSONResponse,
)
async def get_datasources(
    site_list: Optional[List[str]] = Query(None),
    ts_classes: Optional[List[str]] = Query(None),
):
    if site_list is None:
        site_list_response = await get_site_list()
        site_list = site_list_response["_return"]["sites"]

    get_datasources_by_site = {
        "function": "get_datasources_by_site",
        "version": 1,
        "params": {"site_list": ",".join(site_list),},
    }

    if ts_classes is not None:
        get_datasources_by_site["params"]["ts_classes"] = ",".join(ts_classes)

    return await send_request(config.HYDSTRA_BASE_URL, payload=get_datasources_by_site)


@router.get(
    "/sites/variables", response_class=ORJSONResponse,
)
async def get_variables(
    site_list: Optional[List[str]] = Query(None),
    datasource: str = "A",
    var_filter: Optional[List[str]] = Query(None),
):

    if site_list is None:
        site_list_response = await get_site_list()
        site_list = site_list_response["_return"]["sites"]

    get_variable_list = {
        "function": "get_variable_list",
        "version": 1,
        "params": {
            "site_list": None if not site_list else ",".join(site_list),
            "datasource": datasource,
            "var_filter": None if not var_filter else ",".join(var_filter),
        },
    }

    return await send_request(config.HYDSTRA_BASE_URL, payload=get_variable_list)


@router.get(
    "/sites/{site}/variables/{variable}", response_class=ORJSONResponse,
)
async def get_site_variables(
    site: str, variable: Optional[str] = None, datasource: str = "A",
):

    get_variable_list = {
        "function": "get_variable_list",
        "version": 1,
        "params": {
            "site_list": site,
            "datasource": datasource,
            "var_filter": variable,
        },
    }

    return await send_request(config.HYDSTRA_BASE_URL, payload=get_variable_list)


@router.get(
    "/sites/traces", response_class=ORJSONResponse,
)
async def get_trace(
    site_list: List[str] = Query(...),
    start_time: str = Query(...),
    var_list: List[str] = Query(...),
    interval: hydstra_models.Interval = Query(...),
    datasource: str = Query(...),
    end_time: str = Query(...),
    data_type: hydstra_models.DataType = Query(...),
    interval_multiplier: int = Query(1),
    recent_points: Optional[int] = Query(None),
    **kwargs,
):

    ts_trace = {
        "function": "get_ts_traces",
        "version": 2,
        "params": {
            "site_list": ",".join(site_list),
            "start_time": start_time,
            "var_list": ",".join(var_list),
            "interval": interval,
            "datasource": datasource,
            "end_time": end_time,
            "data_type": data_type,
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

    return await send_request(config.HYDSTRA_BASE_URL, payload=ts_trace)


@router.get(
    "/variables/info", response_class=ORJSONResponse,
)
@router.post(
    "/variables/info", response_class=ORJSONResponse,
)
async def get_variables_db_info(
    return_type: Optional[hydstra_models.ReturnType] = "array",
    filter_values: Optional[Dict] = Body({}, example={"active": True}),
):
    get_db_info = {
        "function": "get_db_info",
        "version": "3",
        "params": {
            "table_name": "variable",
            "return_type": return_type,
            "filter_values": filter_values,
        },
    }

    return await send_request(config.HYDSTRA_BASE_URL, payload=get_db_info)


@router.get("/sites/variables/mapping", response_class=ORJSONResponse)
async def get_site_variable_map():

    promise = await get_variables(None, "A", None)
    vars_by_site = []
    for blob in promise["_return"]["sites"]:
        site = blob["site"]
        for variable in blob["variables"]:
            variable["site"] = site
            vars_by_site.append(variable)
    variables = pandas.DataFrame(vars_by_site)

    use_vars = {
        "Rainfall": {"agg": "tot"},  # hydstra codes, not pandas ones.
        "Discharge": {"agg": "mean"},
    }
    variables = variables.merge(
        variables.query("name in @use_vars.keys()")
        .groupby(["site", "name"])
        .variable.min()  # <-- use the minimum number as the 'preferred value for now. Just a WAG.'
        .reset_index()
        .assign(preferred=True)
        .set_index(["site", "name", "variable"])["preferred"],
        left_on=["site", "name", "variable"],
        right_index=True,
        how="left",
    ).fillna(False)

    mapping = (
        variables.query("preferred")
        .assign(label=lambda df: df["name"] + "-" + df["variable"])
        .groupby(["site"])
        .apply(
            lambda x: x[["label", "variable"]].set_index("label").to_dict()["variable"]
        )
    )

    return mapping
