from typing import Any, Dict, List, Optional, Type, Union
from textwrap import dedent

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import ORJSONResponse, HTMLResponse
import pandas

from lyra.api.security import authenticate_admin_access
from lyra.connections import database
from lyra.models.response_models import ForegroundTaskJSONResponse
from lyra.site.style import render_in_jupyter_notebook_css_style
from lyra.core.cache import redis_cache


router = APIRouter(default_response_class=ORJSONResponse)


@router.get(
    "/tables",
    tags=["admin"],
    dependencies=[Depends(authenticate_admin_access)],
    response_model=ForegroundTaskJSONResponse,
)
def get_tables(r: Request):
    tables = []
    response = {}
    try:
        tables = database.engine.table_names()
    except Exception as e:
        response["errors"] = [str(e)]
        return response

    response["data"] = {"tables": tables}
    return response


@router.get(
    "/tables/{table}",
    tags=["admin"],
    dependencies=[Depends(authenticate_admin_access)],
    response_model=ForegroundTaskJSONResponse,
)
def get_tables(
    table: str, limit_to: int = 25, ascending: bool = False, f: str = "json",
):
    data = {}
    response = {}

    try:
        qry = dedent(
            f"""\
        select
            top (?) *
        from [{table}]
        order by
            id {"ASC" if ascending else "DESC"}
        """
        )

        with database.engine.begin() as conn:
            df = pandas.read_sql(qry, params=(limit_to,), con=conn,)

    except Exception as e:
        response["status"] = "FAILURE"
        response["errors"] = [str(e)]
        return response

    if f == "html":
        return HTMLResponse(render_in_jupyter_notebook_css_style(df))

    response["data"] = {"records": df.to_dict(orient="records")}

    return response


@router.get(
    "/clear_cache",
    tags=["admin"],
    dependencies=[Depends(authenticate_admin_access)],
    response_model=ForegroundTaskJSONResponse,
)
async def clear_cache():
    cleared = False
    try:  # pragma: no cover
        # if redis is available, let's flush the cache to start
        # fresh.
        if redis_cache.ping():
            redis_cache.flushdb()
            cleared = True

    except:  # pragma: no cover
        pass

    return {"data": {"cleared": cleared}}
