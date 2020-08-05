from typing import Any, Dict, List, Optional, Union
import requests
import pandas
import altair as alt
from altair.utils.data import MaxRowsError

alt.data_transformers.disable_max_rows()


# from celery.result import AsyncResult
from fastapi import APIRouter, Body, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.requests import Request
from fastapi.responses import ORJSONResponse
from fastapi.templating import Jinja2Templates


from lyra.core import config
from lyra.api.endpoints.hydstra import get_trace
from lyra.models import hydstra_models


router = APIRouter(default_response_class=ORJSONResponse)


@router.get("/trace")
async def plot_trace(
    request: Request,
    site: str,
    start_date: str,
    variable: List[str] = Query(...),
    interval: hydstra_models.Interval = Query(...),
    datasource: str = Query(...),
    end_date: str = Query(...),
    data_type: hydstra_models.DataType = Query(...),
    interval_multiplier: int = 1,
    recent_points: Optional[int] = None,
):

    kwargs = dict(request.query_params)
    for d in ["start_date", "end_date"]:
        kwargs[d.replace("date", "time")] = parse_datetime(
            kwargs.pop(d), kwargs.pop(d.replace("date", "time"), "0")
        )

    kwargs["site_list"] = [kwargs.get("site", "ELTORO")]
    kwargs["var_list"] = [kwargs.get("variable", "11")]
    kwargs["datasource"] = kwargs.get("datasource", "A")
    kwargs["interval_multiplier"] = kwargs.get("multiplier", "1")
    kwargs["recent_points"] = None

    chart_spec = None
    chart_status = None
    msg = ""

    response = await get_trace(**kwargs)

    if response.get("_return") is None:
        msg += f"ERROR in response {response}"
        return {"chart_status": "FAILURE", "message": msg}

    traces = response["_return"]["traces"]

    dfs = []
    for i, trace in enumerate(traces):
        data = trace["trace"]
        site = trace["site"]
        var = trace["varto_details"]["variable"] + "_" + str(i)

        df = (
            pandas.DataFrame(data)
            .assign(date=lambda df: pandas.to_datetime(df["t"], format="%Y%m%d%H%M%S"))
            .assign(values=lambda df: df.v.astype(float))
            .assign(label="-".join([site, var]))
            .assign(
                _thin=lambda df: df["values"]
                - df["values"].shift(1)
                + df["values"].shift(-1)
                != 0.0
            )
            .query("_thin")
            .reindex(columns=["date", "values", "label"])
        )

        dfs.append(df)

    source = pandas.concat(dfs)

    try:
        chart_spec = make_chart(source).to_json()
        chart_status = "SUCCESS"
        if len(source) > 8000:
            msg += f"Warning: {len(source):,g} data points were requested. Consider using a larger ' interval multiplier'."

    except MaxRowsError:
        chart_status = "FAILURE"
        msg += "max data exceeded. Default max is 5000 data points"

    response = {"spec": chart_spec, "chart_status": chart_status, "message": msg}

    return response


def parse_datetime(date: str, time: str) -> str:
    date = date.replace("-", "").ljust(8, "0")
    time = time.replace(":", "").ljust(6, "0")
    return date + time


def make_chart(source):

    line = alt.Chart(source).mark_line().encode(x="date:T", y="values:Q", color="label")

    nearest = alt.selection(
        type="single", nearest=True, on="mouseover", fields=["date"], empty="none"
    )

    selectors = (
        alt.Chart(source)
        .mark_point()
        .encode(x="date:T", y="values:Q", opacity=alt.value(0),)
        .add_selection(nearest)
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align="left", dx=5, dy=-5).encode(
        text=alt.condition(nearest, "values:Q", alt.value(" "))
    )

    # Draw a rule at the location of the selection
    rules = (
        alt.Chart(source)
        .mark_rule(color="gray")
        .encode(x="date:T",)
        .transform_filter(nearest)
    )

    return alt.layer(line, selectors, points, rules, text)
