import time
from typing import Dict, List, Optional, Union

import orjson
from altair.utils.data import MaxRowsError
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import ORJSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from lyra.api.requests import LyraRoute
from lyra.core.errors import HydstraIOError
from lyra.models.plot_models import (
    DiversionScenarioSchema,
    ListTimeseriesSchema,
    MultiVarSchema,
    RegressionSchema,
)
from lyra.models.request_models import (
    AggregationMethod,
    Interval,
    RegressionMethod,
    ResponseDataFormat,
    ResponseFormat,
    Weather,
)
from lyra.models.response_models import ChartJSONResponse
from lyra.src.viz import diversion_scenario, multi_variable, regression

router = APIRouter(route_class=LyraRoute, default_response_class=ORJSONResponse)
templates = Jinja2Templates(directory="lyra/site/templates")

### Timeseries
def timeseries_schema_query(
    timeseries: Optional[str] = Query(
        None,
        example='[{"site":"ALISO_STP","variable":"discharge"},{"site":"ALISO_JERONIMO","variable":"discharge"}]',
    ),
    string: Optional[str] = Query(None, alias="json",),
) -> MultiVarSchema:
    try:
        if string is not None:
            json_parsed = orjson.loads(string)
            rsp = MultiVarSchema(**json_parsed)
        else:
            rsp = MultiVarSchema(timeseries=timeseries)  # type: ignore

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    except orjson.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return rsp


@router.get("/timeseries", response_model=ChartJSONResponse)
def plot_timeseries_with_GET(
    request: Request,
    req: MultiVarSchema = Depends(timeseries_schema_query),
    f: ResponseFormat = Query("json"),
) -> Dict:  # pragma: no cover
    chart_spec = None
    chart_status = None
    msg = []

    try:
        ts = multi_variable.make_timeseries(jsonable_encoder(req.timeseries))
        source = multi_variable.make_source(ts)

        warnings = ["\n".join(t.kwargs.get("warnings", [])) for t in ts]
        msg += warnings

        chart = multi_variable.make_plot(source)
        chart_spec = chart.to_dict()
        chart_status = "SUCCESS"

    except HydstraIOError as e:
        chart_status = "FAILURE"
        msg += [str(e)]

    except MaxRowsError:
        chart_status = "FAILURE"
        msg += ["max data exceeded. Default max is 5000 data points"]

    chart_pkg = {
        "spec": chart_spec,
        "chart_status": chart_status,
        "messages": msg,
    }

    response = {"data": chart_pkg}

    if f == "html":
        return templates.TemplateResponse(  # type: ignore
            "anyspec.html", {"request": request, "response": response,},
        )

    return response


@router.post("/timeseries", response_model=ChartJSONResponse)
def plot_timeseries_with_POST(
    request: Request,
    f: ResponseFormat = Query("json"),
    timeseries: ListTimeseriesSchema = Body(
        ...,
        examples={
            "normal_single": {
                "summary": "A normal single timeseries example",
                "description": "A **normal** single timeseries works correctly.",
                "value": {
                    "timeseries": [
                        {
                            "site": "ALISO_JERONIMO",
                            "variable": "discharge",
                            "interval": "month",
                            "aggregation_method": "mean",
                        }
                    ]
                },
            },
            "normal_multiple": {
                "summary": "A normal multiple timeseries example",
                "description": "A **normal** multiple timeseries works correctly",
                "value": {
                    "timeseries": [
                        {"site": "ALISO_JERONIMO", "variable": "discharge",},
                        {"site": "ALISO_STP", "variable": "discharge",},
                    ]
                },
            },
            "invalid_aggregation": {
                "summary": "Invalid data is rejected with an error",
                "description": (
                    """The method `sum` is not an allowed aggregation_method. 
                    The error response and JSONSchema will reveal valid enums."""
                ),
                "value": {
                    "timeseries": [
                        {
                            "site": "ALISO_JERONIMO",
                            "variable": "discharge",
                            "aggregation_method": "sum",
                        }
                    ]
                },
            },
            "unavailable_aggregation": {
                "summary": "valid aggregations may be unavailable for certain sites & variables",
                "description": (
                    """The method `tot` is an allowed aggregation_method 
                    but it's use doesn't make sense here since discharge is in (cfs). 
                    Rather than erroring, the response uses the 'mean' method rather than 
                    tot for this variable.
                    </br></br>
                    In this case, a list of messages is sent with the chart data as 
                    `response_json['data']['messages']` so that they can be passed to the 
                    end user as a warning.
                    """
                ),
                "value": {
                    "timeseries": [
                        {
                            "site": "ALISO_JERONIMO",
                            "variable": "discharge",
                            "start_date": "2010-01-01",
                            "end_date": "2010-03-01",
                            "aggregation_method": "tot",
                        }
                    ]
                },
            },
        },
    ),
) -> Dict:  # pragma: no cover
    chart_spec = None
    chart_status = None
    msg = []

    try:
        ts = multi_variable.make_timeseries(jsonable_encoder(timeseries.timeseries))
        source = multi_variable.make_source(ts)
        warnings = ["\n".join(t.warnings) for t in ts]
        msg += warnings

        if source.empty:
            msg.append("Warning: No data to display.")

        chart = multi_variable.make_plot(source)
        chart_spec = chart.to_dict()
        chart_status = "SUCCESS"

    except HydstraIOError as e:
        chart_status = "FAILURE"
        msg += [str(e)]

    except MaxRowsError:
        chart_status = "FAILURE"
        msg.append("max data exceeded. Default max is 5000 data points")

    chart_pkg = {
        "spec": chart_spec,
        "chart_status": chart_status,
        "messages": msg,
    }

    response = {"data": chart_pkg}

    if f == "html":
        return templates.TemplateResponse(  # type: ignore
            "anyspec.html", {"request": request, "response": response,},
        )

    return response


### Multi-Var
def multi_var_schema_query(
    request: Request,
    timeseries: Optional[str] = Query(
        None,
        example='[{"site":"ALISO_STP","variable":"discharge"},{"site":"ALISO_JERONIMO","variable":"discharge"}]',
    ),
    site: Optional[str] = Query(None, example="ALISO_JERONIMO"),
    interval: Optional[Interval] = Query("month"),
    weather_condition: Optional[Weather] = Query("both"),
    aggregation_method: Optional[AggregationMethod] = Query("mean"),
    trace_upstream: Optional[bool] = Query(True),
    nearest_rainfall_station: Optional[str] = Query(None, example="ALISO_JERONIMO"),
    start_date: Optional[str] = Query(None, example="2015-01-01"),
    end_date: Optional[str] = Query(None, example="2020-01-01"),
    string: Optional[str] = Query(None, alias="json",),
) -> MultiVarSchema:
    try:  # pragma: no branch
        if string is not None:
            json_parsed = orjson.loads(string)
            rsp = MultiVarSchema(**json_parsed)
        else:
            rsp = MultiVarSchema(**dict(request.query_params))  # type: ignore

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    except orjson.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return rsp


@router.get(
    "/multi_variable", response_model=ChartJSONResponse,
)
def plot_multi_variable(
    request: Request,
    req: MultiVarSchema = Depends(multi_var_schema_query),
    f: ResponseFormat = Query("json"),
) -> Dict:
    """Create Multiple Timeseries Plots

    ### Examples
    
    **as query**
    * api/plot/multi_variable?start_date=2020-03-01&timeseries=[{"site":"ALISO_STP","variable":"urban_drool"},{"site":"ALISO_JERONIMO","variable":"discharge"}]
    
    **as blob**
    * api/plot/multi_variable?json={"start_date":"2020-03-01","timeseries":[{"site":"ALISO_STP","variable":"urban_drool"},{"site":"ALISO_JERONIMO","variable":"discharge"}]}
    * api/plot/multi_variable?json={"start_date":"2020-03-01","end_date":"2021-05-01","site":"ALISO_JERONIMO","timeseries":[{"variable":"rainfall"},{"variable":"discharge"}]}
    """

    req_start = time.perf_counter()

    chart_spec = None
    chart_status = None
    msg = []

    try:  # pragma: no branch
        hyd_start = time.perf_counter()
        ts = multi_variable.make_timeseries(jsonable_encoder(req.timeseries))
        hyd_end = time.perf_counter()

        source_start = time.perf_counter()
        source = multi_variable.make_source(ts)
        source_end = time.perf_counter()

        warnings = ["\n".join(t.warnings) for t in ts]
        msg += warnings

        if source.empty:
            msg.append("Warning: No data to display.")

        plot_start = time.perf_counter()
        chart = multi_variable.make_plot(source)
        plot_end = time.perf_counter()

        chart_spec_start = time.perf_counter()
        chart_spec = chart.to_dict()
        chart_status = "SUCCESS"
        chart_spec_end = time.perf_counter()

    except HydstraIOError as e:
        chart_status = "FAILURE"
        msg += [str(e)]

    except MaxRowsError:
        chart_status = "FAILURE"
        msg += ["max data exceeded. Default max is 5000 data points"]

    chart_pkg = {
        "spec": chart_spec,
        "chart_status": chart_status,
        "messages": msg,
    }

    response = {
        "data": chart_pkg,
        "timings": {
            "hydstra_time_seconds": hyd_end - hyd_start,
            "source_time_seconds": source_end - source_start,
            "plot_time_seconds": plot_end - plot_start,
            "chart_spec_time_seconds": chart_spec_end - chart_spec_start,
            "request_time_seconds": time.perf_counter() - req_start,
        },
    }

    if f == "html":
        return templates.TemplateResponse(  # type: ignore
            "anyspec.html",
            {"request": request, "response": response, "title": "Timeseries"},
        )

    return response


@router.get("/multi_variable/data")
def plot_multi_variable_data(
    req: MultiVarSchema = Depends(multi_var_schema_query),
    f: ResponseDataFormat = Query("json", description="Data format of the response"),
) -> Union[ORJSONResponse, PlainTextResponse]:

    try:  # pragma: no branch
        ts = multi_variable.make_timeseries(jsonable_encoder(req.timeseries))
        source = multi_variable.make_source(ts)
        warnings = ["\n".join(t.warnings) for t in ts]

    except HydstraIOError as e:
        return ORJSONResponse({"error": str(e)})

    if f == "csv":
        csv = multi_variable.make_source_csv(source)
        return PlainTextResponse(csv)
    else:
        _json = jsonable_encoder(multi_variable.make_source_json(source))
        return ORJSONResponse(_json)


## regressions
def regression_schema_query(
    request: Request,
    interval: Optional[Interval] = Query("day"),
    weather_condition: Optional[Weather] = Query("both"),
    regression_method: Optional[RegressionMethod] = Query("linear"),
    start_date: Optional[str] = Query(None, example="2019-01-01"),
    end_date: Optional[str] = Query(None, example="2020-01-01"),
    timeseries: Optional[str] = Query(
        None,
        example='[{"site":"ALISO_STP","variable":"discharge"},{"site":"ALISO_JERONIMO","variable":"discharge"}]',
    ),
    string: Optional[str] = Query(None, alias="json",),
) -> RegressionSchema:
    try:  # pragma: no branch
        if string is not None:
            json_parsed = orjson.loads(string)
            rsp = RegressionSchema(**json_parsed)
        else:
            rsp = RegressionSchema(**dict(request.query_params))  # type: ignore

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    except orjson.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return rsp


@router.get(
    "/regression", response_model=ChartJSONResponse,
)
def plot_regression(
    request: Request,
    req: RegressionSchema = Depends(regression_schema_query),
    f: ResponseFormat = Query("json"),
) -> Dict:
    """Create Pair-Wise Regression Plot

    ### Examples
    
    **as query**
    * api/plot/regression?start_date=2019-01-01&interval=day&site=ALISO_JERONIMO&weather_condition=wet&timeseries=[{"variable":"rainfall"},{"variable":"discharge"}]
    
    **as blob**
    * api/plot/regression?json={"start_date":"2019-01-01","site":"ALISO_JERONIMO","interval":"day","weather_condition":"wet","timeseries":[{"variable":"rainfall"},{"variable":"discharge"}]}
    """

    chart_spec = None
    chart_status = None
    msg = []

    try:  # pragma: no branch
        ts = regression.make_timeseries(**jsonable_encoder(req))
        source = regression.make_source(ts, method=req.regression_method)
        warnings = ["\n".join(t.warnings) for t in ts]
        msg += warnings

        if source.empty:
            msg.append("Warning: No data to display.")

        chart = regression.make_plot(source, method=req.regression_method)
        chart_spec = chart.to_dict()
        chart_status = "SUCCESS"

    except HydstraIOError as e:
        chart_status = "FAILURE"
        msg += [str(e)]

    except MaxRowsError:
        chart_status = "FAILURE"
        msg += ["max data exceeded. Default max is 5000 data points"]

    chart_pkg = {
        "spec": chart_spec,
        "chart_status": chart_status,
        "messages": msg,
    }

    response = {"data": chart_pkg}

    if f == "html":
        return templates.TemplateResponse(  # type: ignore
            "anyspec.html",
            {"request": request, "response": response, "title": "Regression Analysis"},
        )

    return response


@router.get("/regression/data")
def plot_regression_data(
    req: RegressionSchema = Depends(regression_schema_query),
    f: ResponseDataFormat = Query("json", description="Data format of the response"),
) -> Union[ORJSONResponse, PlainTextResponse]:
    try:  # pragma: no branch
        ts = regression.make_timeseries(**jsonable_encoder(req))
        source = regression.make_source(ts, method=req.regression_method)
        warnings = ["\n".join(t.warnings) for t in ts]

    except HydstraIOError as e:
        return ORJSONResponse({"error": str(e)})

    if f == "csv":
        csv = regression.make_source_csv(source)
        return PlainTextResponse(csv)
    else:
        _json = jsonable_encoder(regression.make_source_json(source))
        return ORJSONResponse(_json)


### Diversion Scenario
def diversion_scenario_schema_query(
    request: Request,
    site: Optional[str] = Query(None, example="ALISO_STP"),
    start_date: Optional[str] = Query(None, example="2021-05-01"),
    end_date: Optional[str] = Query(None, example="2021-08-01"),
    diversion_rate_cfs: Optional[float] = Query(None, example=3.5),
    storage_max_depth_ft: Optional[float] = 0.0,
    storage_initial_depth_ft: Optional[float] = 0.0,
    storage_area_sqft: Optional[float] = 0.0,
    infiltration_rate_inhr: Optional[float] = 0.0,
    rainfall_event_shutdown: Optional[bool] = True,
    rainfall_event_depth_threshold: Optional[float] = 0.1,
    event_separation_hrs: Optional[float] = 6.0,
    after_rain_delay_hrs: Optional[float] = 72.0,
    diversion_months_active: Optional[List[int]] = Query(None),
    diversion_days_active: Optional[List[int]] = Query(None),
    diversion_hours_active: Optional[List[int]] = Query(None),
    nearest_rainfall_station: Optional[str] = None,
    string: Optional[str] = Query(None, alias="json",),
) -> DiversionScenarioSchema:
    try:  # pragma: no branch
        if string is not None:
            json_parsed = orjson.loads(string)
            rsp = DiversionScenarioSchema(**json_parsed)
        else:
            rsp = DiversionScenarioSchema(**dict(request.query_params))  # type: ignore

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    except orjson.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return rsp


@router.get(
    "/diversion_scenario", response_model=ChartJSONResponse,
)
def plot_diversion_scenario(
    request: Request,
    req: DiversionScenarioSchema = Depends(diversion_scenario_schema_query),
    f: ResponseFormat = Query("json"),
) -> Dict:
    """Create Diversion Scenario Plots
    """

    chart_spec = None
    chart_status = None
    msg = []

    try:  # pragma: no branch
        # ts = multi_variable.make_timeseries(jsonable_encoder(req.timeseries))
        source = diversion_scenario.make_source(**jsonable_encoder(req))
        # warnings = ["\n".join(t.warnings) for t in ts]
        # msg += warnings

        if source.empty:
            msg.append("Warning: No data to display.")

        table = diversion_scenario.make_summary_table(source)

        chart = diversion_scenario.make_plot(source)
        chart_spec = chart.to_dict()
        chart_status = "SUCCESS"

    except HydstraIOError as e:
        chart_status = "FAILURE"
        msg += [str(e)]

    except MaxRowsError:
        chart_status = "FAILURE"
        msg += ["max data exceeded. Default max is 5000 data points"]

    chart_pkg = {
        "spec": chart_spec,
        "chart_status": chart_status,
        "messages": msg,
        "table": table,
    }

    response = {"data": chart_pkg}

    if f == "html":
        return templates.TemplateResponse(  # type: ignore
            "anyspec.html",
            {"request": request, "response": response, "title": "Diversion Scenario"},
        )

    return response


@router.get("/diversion_scenario/data")
def plot_diversion_scenario_data(
    req: DiversionScenarioSchema = Depends(diversion_scenario_schema_query),
    f: ResponseDataFormat = Query("json", description="Data format of the response"),
) -> Union[ORJSONResponse, PlainTextResponse]:

    try:  # pragma: no branch
        # ts = multi_variable.make_timeseries(jsonable_encoder(req.timeseries))
        source = diversion_scenario.make_source(**jsonable_encoder(req))
        # warnings = ["\n".join(t.warnings) for t in ts]

    except HydstraIOError as e:
        return ORJSONResponse({"error": str(e)})

    if f == "csv":
        csv = diversion_scenario.make_source_csv(source)
        return PlainTextResponse(csv)
    else:
        _json = jsonable_encoder(diversion_scenario.make_source_json(source))
        return ORJSONResponse(_json)
