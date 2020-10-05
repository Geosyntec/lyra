import json
from typing import List, Optional
from urllib.parse import urlencode

import altair as alt
import orjson
import pandas
from altair.utils.data import MaxRowsError
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import ORJSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from lyra.models import hydstra_models
from lyra.models.plot_models import SingleVarSpec
from lyra.models.response_models import ChartJSONResponse, RawJSONResponse
from lyra.src.hydstra.api import get_trace
from lyra.src.hydstra.helper import to_hydstra_datetime
from lyra.src.viz import single_variable

alt.data_transformers.disable_max_rows()

router = APIRouter(default_response_class=ORJSONResponse)
templates = Jinja2Templates(directory="lyra/site/templates")


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
):  # pragma: no cover

    kwargs = dict(request.query_params)
    for d in ["start_date", "end_date"]:
        kwargs[d.replace("date", "time")] = to_hydstra_datetime(
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


def make_chart(source):  # pragma: no cover

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


def single_var_spec_query(
    variable: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    sites: Optional[List[str]] = Query(None),
    intervals: Optional[List[str]] = Query(None),
    trace_upstreams: Optional[List[bool]] = Query(None),
    agg_methods: Optional[List[str]] = Query(None),
    string: Optional[str] = Query(None, alias="json"),
):

    try:
        if string is not None:
            rsp = SingleVarSpec(**orjson.loads(string))
        else:
            rsp = SingleVarSpec(
                variable=variable,
                sites=sites,
                start_date=start_date,
                end_date=end_date,
                intervals=intervals,
                trace_upstreams=trace_upstreams,
                agg_methods=agg_methods,
            )

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    return rsp


@router.get("/single_variable", response_model=ChartJSONResponse)
def plot_single_variable(
    request: Request,
    req: SingleVarSpec = Depends(single_var_spec_query),
    f: str = Query("json"),
):

    chart_spec = None
    chart_status = None
    msg = ""

    qp = urlencode(req.dict(exclude_none=True), doseq=True)
    url = request.url_for("plot_single_variable_data") + "?" + qp

    try:
        # chart = single_variable.dispatch(**req.dict())
        chart = single_variable.make_plot(url)
        chart_spec = chart.to_dict()
        chart_status = "SUCCESS"
        # if len(source) > 8000:
        #     msg += f"Warning: {len(source):,g} data points were requested. Consider using a larger 'interval multiplier'."

    except MaxRowsError:
        chart_status = "FAILURE"
        msg += "max data exceeded. Default max is 5000 data points"

    chart_pkg = {
        "spec": chart_spec,
        "chart_status": chart_status,
        "message": msg,
    }

    response = {"data": chart_pkg}

    if f == "html":
        return templates.TemplateResponse(
            "anyspec.html", {"request": request, "response": response,},
        )

    return response


@router.get(
    "/single_variable/data",
    # response_class=RawJSONResponse
)
def plot_single_variable_data(
    req: SingleVarSpec = Depends(single_var_spec_query), f: str = Query("json"),
):
    src = single_variable.make_source(**req.dict())
    if f == "csv":
        csv = single_variable.make_source_csv(src)
        return PlainTextResponse(csv)
    else:
        return single_variable.make_source_json(src)
