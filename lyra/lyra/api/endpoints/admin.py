from textwrap import dedent

from fastapi import APIRouter, Depends, Request
from fastapi.responses import ORJSONResponse, HTMLResponse
import pandas
from sqlalchemy import sql, select, desc, text

from lyra.core import security
from lyra.core import cache
from lyra.connections import database
from lyra.models.response_models import ForegroundTaskJSONResponse
from lyra.site.style import render_in_jupyter_notebook_css_style


router = APIRouter(default_response_class=ORJSONResponse)


@router.get(
    "/tables",
    dependencies=[Depends(security.authenticate_admin_access)],
    response_model=ForegroundTaskJSONResponse,
)
async def get_table_names(r: Request):
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
    dependencies=[Depends(security.authenticate_admin_access)],
    response_model=ForegroundTaskJSONResponse,
)
async def get_table_content(
    table: str, limit_to: int = 25, ascending: bool = False, f: str = "json",
):
    data = {}
    response = {}

    try:
        table = sql.table(table)
        order_by = text("id")
        if not ascending:
            order_by = desc(order_by)

        s = select([table, "*"]).limit(limit_to).order_by(order_by)

        with database.engine.begin() as conn:
            df = pandas.read_sql(s, con=conn)

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
    dependencies=[Depends(security.authenticate_admin_access)],
    response_model=ForegroundTaskJSONResponse,
)
async def clear_cache():  # pragma: no cover
    cleared = False
    try:
        cache.flush()
        cleared = True
    except Exception as e:
        pass

    return {"data": {"cleared": cleared}}


@router.get(
    "/toggle_cache",
    dependencies=[Depends(security.authenticate_admin_access)],
    response_model=ForegroundTaskJSONResponse,
)
async def toggle_cache(enabled: bool = True):
    cache.use_cache(enabled)

    return {"data": {"ENABLE_REDIS_CACHE": enabled}}
