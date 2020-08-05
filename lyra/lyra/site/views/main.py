from pathlib import Path
import json

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from lyra.api.endpoints import hydstra
import lyra

router = APIRouter()

templates = Jinja2Templates(directory="lyra/site/templates")


@router.get("/")
@router.get("/home")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/timeseries", tags=["demo"])
async def timeseriesfunc(request: Request):

    sitelist_file = Path(lyra.__file__).parent / "static" / "site_list.json"
    sitelist = json.loads(sitelist_file.read_text())["sites"]

    plot_function_url = "./api/plot/trace"
    return templates.TemplateResponse(
        "timeseries.html",
        {
            "request": request,
            "sitelist": sitelist,
            "plot_function_url": plot_function_url,
        },
    )


@router.get("/test_cors")
async def test_corsfunc(request: Request):

    return templates.TemplateResponse("test_cors.html", {"request": request})


@router.get("/map", tags=["demo"])
async def get_map(
    request: Request, toposimplify: float = 0.0001, topoquantize: float = 1e6
):
    topo_url = f"./api/mnwd/spatial/rsb_json?f=topojson&timeout=120&toposimplify={toposimplify}&topoquantize={topoquantize}"
    return templates.TemplateResponse(
        "map.html", {"request": request, "topo_url": topo_url}
    )
