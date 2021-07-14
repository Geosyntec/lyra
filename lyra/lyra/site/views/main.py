import json
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Query, Request, Response
from fastapi.templating import Jinja2Templates

import lyra
from lyra.api.requests import LyraRoute
from lyra.core.config import cfg
from lyra.core.io import load_file

router = APIRouter(route_class=LyraRoute)

templates = Jinja2Templates(directory="lyra/site/templates")


@router.get("/", include_in_schema=False)
@router.get("/home", include_in_schema=False)
async def home(request: Request) -> Response:
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/timeseries", tags=["deprecated"])
async def timeseriesfunc(request: Request) -> Response:

    # sitelist_file = Path(lyra.__file__).parent / "static" / "site_list.json"
    # sitelist = json.loads(sitelist_file.read_text())["sites"]

    site_props = [
        f["properties"] for f in json.loads(load_file(cfg["site_path"]))["features"]
    ]
    sitelist = [d["station"] for d in site_props]

    plot_function_url = request.url_for("plot_trace")
    return templates.TemplateResponse(
        "timeseries.html",
        {
            "request": request,
            "sitelist": sitelist,
            "plot_function_url": plot_function_url,
        },
    )


@router.get("/single_variable", tags=["deprecated"])
async def site_single_variable(request: Request) -> Response:

    sitelist_file = Path(lyra.__file__).parent / "static" / "preferred_variables.json"
    site_vars = json.loads(sitelist_file.read_text())

    plot_function_url = request.url_for("plot_single_variable")
    return templates.TemplateResponse(
        "single_var.html",
        {
            "request": request,
            "site_vars": site_vars,
            "plot_function_url": plot_function_url,
        },
    )


@router.get("/test_cors", include_in_schema=False)
async def test_corsfunc(request: Request) -> Response:

    return templates.TemplateResponse("test_cors.html", {"request": request})


@router.get("/map", tags=["demo", "spatial"])
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

    topo_url = f"./api/spatial/regional_subbasins?f=topojson"
    # topo_url = f"./data/mount/swn/mnwd/drooltool/spatial/rsb_topo_4326_latest.json"
    geo_url = f"./api/spatial/regional_subbasins?f=geojson"
    sites_url = "./api/spatial/site_info"

    # if params:
    #     topo_url += "&" + urlencode(params, doseq=True)
    #     geo_url += "&" + urlencode(params, doseq=True)

    return templates.TemplateResponse(
        "map.html",
        {
            "request": request,
            "topo_url": topo_url,
            "geo_url": geo_url,
            "sites_url": sites_url,
        },
    )


@router.get("/anyspec", include_in_schema=False)
async def get_anyspec(request: Request) -> Response:
    return templates.TemplateResponse("anyspec.html", {"request": request})
