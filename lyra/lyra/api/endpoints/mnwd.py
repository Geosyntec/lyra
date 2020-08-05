from typing import Any, Dict, List, Optional, Union
from textwrap import dedent

import pandas

from fastapi import APIRouter, Body, Query, Depends
from fastapi.requests import Request
from fastapi.responses import ORJSONResponse, HTMLResponse

import lyra.bg_worker as bg
from lyra.connections import database
from lyra.core.config import settings
from lyra.core.utils import run_task, run_task_kwargs
from lyra.site.style import render_in_jupyter_notebook_css_style

from lyra.models.response_models import (
    ForegroundTaskJSONResponse,
    CeleryTaskJSONResponse,
)

from lyra.ops.mnwd.tasks import rsb_json


RunTaskResponse = Union[CeleryTaskJSONResponse, ForegroundTaskJSONResponse]


router = APIRouter(default_response_class=ORJSONResponse)


@router.get("/spatial/rsb_json", tags=["spatial"], response_model=RunTaskResponse)
@router.post("/spatial/rsb_json", tags=["spatial"], response_model=RunTaskResponse)
async def post_rsb_json(
    f: str = "topojson",
    xmin=None,
    ymin=None,
    xmax=None,
    ymax=None,
    toposimplify: float = 0.0001,
    topoquantize: float = 1e6,
    kwargs: dict = Depends(run_task_kwargs),
) -> Dict[str, Any]:
    task = bg.background_rsb_json.s(
        f=f,
        xmin=xmin,
        ymin=ymin,
        xmax=xmax,
        ymax=ymax,
        toposimplify=toposimplify,
        topoquantize=topoquantize,
    )
    return await run_task(task, get_route="get_update_rsb_geojson", **kwargs)


@router.get(
    "/spatial/rsb_json/{task_id}", tags=["spatial"], response_model=RunTaskResponse
)
async def get_rsb_json(
    task_id: str, kwargs: dict = Depends(run_task_kwargs)
) -> Dict[str, Any]:
    task = bg.background_rsb_json.AsyncResult(task_id, app=router)
    return await run_task(task, **kwargs)


@router.get(
    "/dt_metrics", tags=["drooltool"], response_model=ForegroundTaskJSONResponse,
)
def get_dt_metrics(
    f="json",
    variable: str = "*",
    catchidn: str = "*",
    limit_to: int = 25,
    # table: str, limit_to: int = 25, ascending: bool = False, f: str = "json",
):

    try:
        qry = dedent(
            f"""\
        select
            *
        from [DTMetricsCategories]
        """
        )

        with database.engine.begin() as conn:
            cat = pandas.read_sql(qry, con=conn,)

    except Exception as e:
        response["status"] = "FAILURE"
        response["errors"] = [str(e)]
        return response

    data = {}
    response = {}

    if variable is None or variable == "*":
        variable, user_var = "1=?", str(1)
    else:
        user_var = variable
        variable = "variable=?"

    if catchidn is None or catchidn == "*":
        catchidn, user_catch = "1=?", str(1)
    else:
        user_catch = catchidn
        catchidn = "catchidn=?"

    try:
        qry = dedent(
            f"""\
        select
            top (?) *
        from [DTMetrics]
        where
            {variable} and {catchidn}
        order by
            catchidn ASC, variable ASC, year ASC, month ASC
        """
        )

        with database.engine.begin() as conn:
            df = pandas.read_sql(
                qry, params=(limit_to, user_var, user_catch,), con=conn,
            )

            df = (
                df.assign(var_id=lambda df: df["variable"])
                .drop(columns=["variable"])
                .merge(cat, right_index=True, left_on="var_id")
                .drop(columns=["var_id"])
            )

    except Exception as e:
        response["status"] = "FAILURE"
        response["errors"] = [str(e)]
        return response

    if f == "html":
        return HTMLResponse(render_in_jupyter_notebook_css_style(df))

    response["data"] = {"records": df.to_dict(orient="records")}

    return response
