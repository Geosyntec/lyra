from typing import Any, Dict, List, Optional

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
from lyra.models.response_models import DataResponseFormat, JSONAPIResponse
from lyra.site.style import render_in_jupyter_notebook_css_style

router = APIRouter(default_response_class=ORJSONResponse)


@router.get(
    "/", response_model=JSONAPIResponse,
)
async def get_dt_metrics(
    f: Optional[DataResponseFormat] = "json",
    catchidns: Optional[List[int]] = Query(
        None, description="Filter by catchidn. Default includes all catchidns"
    ),
    variables: Optional[List[str]] = Query(
        None, description="Filter by variable. Default includes all variables"
    ),
    years: Optional[List[int]] = Query(
        None, description="Filter by year. Default includes all years"
    ),
    months: Optional[List[int]] = Query(
        None, description="Filter by month. Default includes all months"
    ),
    groupby: Optional[List[str]] = Query(
        None,
        description='Group data for aggregation. Default is ["variable", "year", "month"]',
    ),
    agg: Optional[str] = Query(
        None,
        description="Aggregation function. Default is None, which performs no aggregation. Use `sum/mean/max/min` or another builtin `pandas` agg function.",
    ),
    kwargs: dict = Depends(run_task_kwargs),
):
    task = bg.background_dt_metrics_response.s(
        catchidns=catchidns,
        variables=variables,
        years=years,
        months=months,
        groupby=groupby,
        agg=agg,
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
