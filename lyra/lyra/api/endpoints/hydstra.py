from typing import Any, Dict, List, Optional, Union
import requests

# from celery.result import AsyncResult
from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.requests import Request
from fastapi.responses import ORJSONResponse
from fastapi.templating import Jinja2Templates

from lyra.core import config


router = APIRouter()


@router.get(
    "/hydstra/sites", response_class=ORJSONResponse,
)
async def get_site_list():
    get_site_list = {
        "function": "get_site_list",
        "version": 1,
        "params": {"site_list": "TSFILES(DSOURCES(tscARCHIVE))"},
    }
    response = requests.post(config.HYDSTRA_BASE_URL, json=get_site_list)
    response.json()
    return response.json()["_return"]


@router.get(
    "/hydstra/sites/info/", response_class=ORJSONResponse,
)
async def get_db_info(
    site: Optional[str] = Query(None),
    fields: Optional[List[str]] = Query(None),
    return_type: str = "array",
):
    get_db_info = {
        "function": "get_db_info",
        "version": "3",
        "params": {"table_name": "site", "return_type": return_type,},
    }
    if site is not None:
        get_db_info["params"]["filter_values"] = {}
        get_db_info["params"]["filter_values"]["station"] = site

    if fields is not None:
        get_db_info["params"]["field_list"] = fields # pass as array

    response = requests.post(config.HYDSTRA_BASE_URL, json=get_db_info)
    return response.json()["_return"]


@router.get(
    "/hydstra/{site}/info/", response_class=ORJSONResponse,
)
async def get_db_info(site: str, format: str = "array"):
    get_db_info = {
        "function": "get_db_info",
        "version": "3",
        "params": {"table_name": "site", "return_type": "array",},
    }

    get_db_info["params"]["filter_values"] = {}
    get_db_info["params"]["filter_values"]["station"] = site

    response = requests.post(config.HYDSTRA_BASE_URL, json=get_db_info)
    return response.json()["_return"]


@router.post(
    "/hydstra/sites/spatial", response_class=ORJSONResponse,
)
async def get_site_geojson(
    sites: Optional[List[str]] = Query(None),
    fields: Optional[List[str]] = Query(None),
    get_elev: Optional[int] = 0,
):

    if sites is None:

        get_site_list = {
            "function": "get_site_list",
            "version": 1,
            "params": {"site_list": "TSFILES(DSOURCES(tscARCHIVE))"},
        }
        response = requests.post(config.HYDSTRA_BASE_URL, json=get_site_list)
        sites = response.json()["_return"]["sites"]

    if fields is None:
        fields = ["station", "latitude", "longitude", "stntype", "stname", "shortname"]

    get_site_geojson = {
        "function": "get_site_geojson",
        "version": 2,
        "params": {"site_list": ",".join(sites), "get_elev": 0, "fields": fields,},
    }

    response = requests.post(config.HYDSTRA_BASE_URL, json=get_site_geojson)
    locations = response.json().get("_return")
    if locations:
        return locations
    return response
