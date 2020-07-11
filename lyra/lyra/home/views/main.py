from pathlib import Path
import json

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from lyra.api.endpoints import hydstra
import lyra

router = APIRouter()

templates = Jinja2Templates(directory="lyra/home/templates")


@router.get("/home")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/timeseries")
async def timeseriesfunc(request: Request):

    sitelist_file = Path(lyra.__file__).parent / "static" / "site_list.json"
    sitelist = json.loads(sitelist_file.read_text())["sites"]

    plot_function = "plot_trace"
    return templates.TemplateResponse(
        "timeseries.html",
        {"request": request, "sitelist": sitelist, "plot_function": plot_function},
    )


@router.get("/test_cors")
async def test_corsfunc(request: Request):

    return templates.TemplateResponse("test_cors.html", {"request": request})
