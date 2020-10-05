from typing import Any, Dict, List, Optional

import networkx
import orjson
import pandas
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, ORJSONResponse

import lyra.bg_worker as bg
from lyra.core.utils import (
    run_task,
    run_task_kwargs,
    wait_a_sec_and_see_if_we_can_return_some_data,
)
from lyra.models.response_models import (
    DataResponseFormat,
    JSONAPIResponse,
    ResponseFormat,
    SpatialResponseFormat,
)
from lyra.site.style import render_in_jupyter_notebook_css_style
from lyra.src.network.algorithms import trace_downstream

router = APIRouter(default_response_class=ORJSONResponse)


@router.get("/spatial", tags=["spatial"], response_model=JSONAPIResponse)
async def get_rsb_spatial(
    f: Optional[SpatialResponseFormat] = "topojson",
    xmin: Optional[float] = None,
    ymin: Optional[float] = None,
    xmax: Optional[float] = None,
    ymax: Optional[float] = None,
    watersheds: Optional[List[str]] = Query(None),
    catchidns: Optional[List[str]] = Query(None),
    toposimplify: float = 0.0001,
    topoquantize: float = 1e6,
    kwargs: dict = Depends(run_task_kwargs),
) -> Dict[str, Any]:
    task = bg.background_rsb_json_response.s(
        f=f,
        xmin=xmin,
        ymin=ymin,
        xmax=xmax,
        ymax=ymax,
        watersheds=watersheds,
        catchidns=catchidns,
        toposimplify=toposimplify,
        topoquantize=topoquantize,
    )
    return await run_task(task, get_route="get_task", **kwargs)


@router.get("/upstream_catchments", response_model=JSONAPIResponse)
async def get_rsb_upstream(
    catchidn: int = Query(
        ..., description="Catchment from which to trace other upstream catchments."
    ),
    kwargs: dict = Depends(run_task_kwargs),
):
    task = bg.background_rsb_upstream_trace_response.s(catchidn=catchidn)
    return await run_task(task, get_route="get_task", **kwargs)


@router.get("/downstream_catchments", response_model=JSONAPIResponse)
async def get_rsb_downstream(
    catchidn: int = Query(
        ..., description="Catchment from which to trace other downstream catchments."
    ),
    kwargs: dict = Depends(run_task_kwargs),
):
    task = bg.background_rsb_downstream_trace_response.s(catchidn=catchidn)
    return await run_task(task, get_route="get_task", **kwargs)


@router.get("/", response_model=JSONAPIResponse)
async def get_rsb_data(
    f: Optional[DataResponseFormat] = "json",
    watersheds: Optional[List[str]] = Query(None),
    catchidns: Optional[List[str]] = Query(None),
    kwargs: dict = Depends(run_task_kwargs),
):

    task = bg.background_rsb_data_response.s(
        watersheds=watersheds, catchidns=catchidns,
    )

    if f == "html":
        task = task.apply_async()

        _ = await wait_a_sec_and_see_if_we_can_return_some_data(
            task, timeout=kwargs["timeout"]
        )

        if task.successful():
            data = orjson.loads(task.result)["data"]
            df = pandas.DataFrame(data)
            return HTMLResponse(render_in_jupyter_notebook_css_style(df))

    return await run_task(task, get_route="get_task", **kwargs)
