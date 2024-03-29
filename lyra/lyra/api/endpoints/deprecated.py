from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import altair as alt
import orjson
import pandas
from altair.utils.data import MaxRowsError
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import ORJSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from lyra.api.requests import LyraRoute
from lyra.models import request_models
from lyra.models.plot_models import SingleVarSpec
from lyra.models.response_models import ChartJSONResponse
from lyra.src.hydstra.api import get_trace
from lyra.src.hydstra.helper import to_hydstra_datetime
from lyra.src.viz import single_variable

router = APIRouter(route_class=LyraRoute, default_response_class=ORJSONResponse)
templates = Jinja2Templates(directory="lyra/site/templates")


@router.get("/trace", include_in_schema=False)
async def plot_trace(
    request: Request,
    site: str,
    start_date: str,
    variable: List[str] = Query(...),
    interval: request_models.Interval = Query(...),
    datasource: str = Query(...),
    end_date: str = Query(...),
    data_type: request_models.AggregationMethod = Query(...),
    interval_multiplier: int = 1,
    recent_points: Optional[int] = None,
) -> Dict:  # pragma: no cover

    kwargs: Dict[str, Any] = dict(request.query_params)
    for d in ["start_date", "end_date"]:
        kwargs[d.replace("date", "time")] = to_hydstra_datetime(
            kwargs.pop(d), kwargs.pop(d.replace("date", "time"), "0")
        )

    kwargs["site_list"] = kwargs.get("site", "ELTORO")
    kwargs["var_list"] = kwargs.get("variable", "11")
    kwargs["datasource"] = kwargs.get("datasource", "PUBLISH")
    kwargs["interval_multiplier"] = kwargs.get("multiplier", "1")
    kwargs["recent_points"] = None

    chart_spec = None
    chart_status = None
    msg = ""

    response = await get_trace(**kwargs)

    if response.get("return") is None:
        msg += f"ERROR in response {response}"
        return {"chart_status": "FAILURE", "message": msg}

    traces = response["return"]["traces"]

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
        type="single", nearest=True, on="mouseover", fields=["date"], empty="none",
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
        .encode(alt.X("date:T"))
        .transform_filter(nearest)
    )

    return alt.layer(line, selectors, points, rules, text)


def single_var_spec_query(
    variable: Optional[str] = Query(None, example="rainfall"),
    start_date: Optional[str] = Query(None, example="2015-01-01"),
    end_date: Optional[str] = Query(None, example="2020-01-01"),
    sites: Optional[List[str]] = Query(None, example=["ELTORO"]),
    intervals: Optional[List[request_models.Interval]] = Query(None, example=["month"]),
    trace_upstreams: Optional[List[bool]] = Query(None, example=[False]),
    agg_methods: Optional[List[request_models.AggregationMethod]] = Query(
        None, example=["tot"]
    ),
    string: Optional[str] = Query(
        None,
        alias="json",
        description="This field superceedes all other query params.",
        example="""\
{
    "variable": "rainfall",
    "sites": ["ELTORO"],
    "start_date": "2015-01-01",
    "end_date": "2020-01-01",
    "intervals": ["month"],
    "trace_upstreams": ["false"],
    "agg_methods": ["mean"]
}""",
    ),
) -> SingleVarSpec:

    try:
        if string is not None:
            rsp = SingleVarSpec(**orjson.loads(string))
        else:
            rsp = SingleVarSpec(
                variable=variable,  # type: ignore
                sites=sites,  # type: ignore
                start_date=start_date,
                end_date=end_date,
                intervals=intervals,
                trace_upstreams=trace_upstreams,
                agg_methods=agg_methods,  # type: ignore
            )

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    return rsp


@router.get(
    "/single_variable", response_model=ChartJSONResponse,  # include_in_schema=False
)
def plot_single_variable(
    request: Request,
    req: SingleVarSpec = Depends(single_var_spec_query),
    f: str = Query("json"),
) -> Dict:

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
        return templates.TemplateResponse(  # type: ignore
            "anyspec.html", {"request": request, "response": response,},
        )

    return response


@router.get("/single_variable/data",)  # include_in_schema=False
def plot_single_variable_data(
    req: SingleVarSpec = Depends(single_var_spec_query), f: str = Query("json")
) -> Union[ORJSONResponse, PlainTextResponse]:
    src = single_variable.make_source(**req.dict())
    if f == "csv":
        csv = single_variable.make_source_csv(src)
        return PlainTextResponse(csv)
    else:
        _json = jsonable_encoder(single_variable.make_source_json(src))
        return ORJSONResponse(_json)
