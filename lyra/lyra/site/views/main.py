import json
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Query, Request, Response
from fastapi.templating import Jinja2Templates

import lyra
from lyra.api.requests import LyraRoute

router = APIRouter(route_class=LyraRoute)

templates = Jinja2Templates(directory="lyra/site/templates")


@router.get("/")
@router.get("/home")
async def home(request: Request) -> Response:
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/timeseries", tags=["demo"])
async def timeseriesfunc(request: Request) -> Response:

    sitelist_file = Path(lyra.__file__).parent / "static" / "site_list.json"
    sitelist = json.loads(sitelist_file.read_text())["sites"]

    plot_function_url = request.url_for("plot_trace")
    return templates.TemplateResponse(
        "timeseries.html",
        {
            "request": request,
            "sitelist": sitelist,
            "plot_function_url": plot_function_url,
        },
    )


@router.get("/single_variable", tags=["demo"])
async def site_single_variable(request: Request) -> Response:

    sitelist_file = Path(lyra.__file__).parent / "static" / "preferred_variables.json"
    site_vars = json.loads(sitelist_file.read_text())
    sequence_keys = ["sites", "intervals", "agg_methods", "trace_upstreams"]

    plot_function_url = request.url_for("plot_single_variable")
    return templates.TemplateResponse(
        "single_var.html",
        {
            "request": request,
            "site_vars": site_vars,
            "sequence_keys": sequence_keys,
            "plot_function_url": plot_function_url,
        },
    )


@router.get("/test_cors")
async def test_corsfunc(request: Request) -> Response:

    return templates.TemplateResponse("test_cors.html", {"request": request})


@router.get("/map", tags=["demo"])
async def get_map(
    request: Request,
    xmin: Optional[float] = None,
    ymin: Optional[float] = None,
    xmax: Optional[float] = None,
    ymax: Optional[float] = None,
    watersheds: Optional[List[str]] = Query(None),
    catchidns: Optional[List[str]] = Query(None),
    toposimplify: float = 0.0001,
    topoquantize: float = 1e6,
) -> Response:

    params = dict(
        xmin=xmin,
        ymin=ymin,
        xmax=xmax,
        ymax=ymax,
        watersheds=watersheds,
        catchidns=catchidns,
        toposimplify=toposimplify,
        topoquantize=topoquantize,
    )

    params = {k: v for k, v in params.items() if v is not None}

    topo_url = f"./api/regional_subbasins/spatial?f=topojson&timeout=120"
    geo_url = f"./api/regional_subbasins/spatial?f=geojson&timeout=120"

    if params:
        topo_url += "&" + urlencode(params, doseq=True)
        geo_url += "&" + urlencode(params, doseq=True)

    return templates.TemplateResponse(
        "map.html", {"request": request, "topo_url": topo_url, "geo_url": geo_url}
    )
