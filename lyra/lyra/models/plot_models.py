import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import orjson
import pytz
from pydantic import BaseModel, Field, root_validator, validator

from lyra.core import utils
from lyra.core.config import cfg
from lyra.core.io import load_file
from lyra.models.request_models import (
    AggregationMethod,
    Interval,
    RegressionMethod,
    Weather,
)

VALID_VARIABLES = list(cfg["variables"].keys())


class SingleVarSpec(BaseModel):
    variable: str
    sites: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    intervals: Optional[List[Interval]] = None
    trace_upstreams: Optional[List[bool]] = None
    agg_methods: Optional[List[str]] = None

    @validator("sites", "intervals", "agg_methods", pre=True)
    def expand_flatten(cls, v):
        if v is not None:
            return utils.flatten_expand_list(v)

    @validator("variable")
    def check_variable(cls, v):
        assert v in VALID_VARIABLES, f"invalid variable: `{v}`"
        return v

    @root_validator
    def check_site_variables(cls, values):
        sites = values.get("sites", [])
        variable = values.get("variable")
        source = cfg.get("variables", {}).get(variable, {}).get("source")

        # load_file will cache this so it doesn't happen for frequent requests
        site_props = [
            f["properties"] for f in json.loads(load_file(cfg["site_path"]))["features"]
        ]
        valid_sites = [d["station"] for d in site_props]

        for site in sites:
            var_info: Dict = next((x for x in site_props if x["station"] == site), {})

            valid_sites = [d["station"] for d in site_props]
            assert (
                site in valid_sites
            ), f"'{site}' is not valid. \n\tOptions are: {valid_sites}"

            if source == "hydstra":
                assert (
                    site in valid_sites
                ), f"'{site}' is not valid. \n\tOptions are: {valid_sites}"
                assert var_info.get(
                    f"has_{variable}"
                ), f"'{variable}' not found at site '{site}'"

        return values

    @root_validator
    def check_agg_methods(cls, values):

        variable = values.get("variable", "no variable")
        allowed_aggs = (
            cfg.get("variables", {}).get(variable, {}).get("allowed_aggregations", [])
        )
        for agg in values.get("agg_methods") or []:
            assert agg in allowed_aggs, f"'{agg}' not allowed for variable '{variable}'"

        return values

    @root_validator
    def check_max_length(cls, values):
        same_length = ["intervals", "trace_upstreams", "agg_methods"]
        n = len(values.get("sites", []))
        for s in same_length:
            v = values.get(s) or []
            assert len(v) <= n, f"count of '{s}' must <= number of sites."
        return values


## Multi Variable


def default_end_date():
    today = datetime.now(pytz.timezone("US/Pacific"))
    today_eod = today + timedelta(days=1)
    return today_eod.date().isoformat()


def default_start_date():
    today = datetime.now(pytz.timezone("US/Pacific"))
    default_duration = timedelta(days=30 * 6)
    startdate = today - default_duration
    return (
        datetime(year=startdate.year, month=startdate.month, day=1).date().isoformat()
    )


class TimeseriesBaseSchema(BaseModel):
    start_date: Optional[str] = Field(None, example="2015-01-01")
    end_date: Optional[str] = Field(None, example="2020-01-01")
    interval: Optional[Interval] = None
    weather_condition: Optional[Weather] = None

    @validator("start_date", pre=True, always=True)
    def set_start_date(cls, start_date):
        return start_date or default_start_date()

    @validator("end_date", pre=True, always=True)
    def set_end_date(cls, end_date):
        return end_date or default_end_date()

    @validator("interval", pre=True, always=True)
    def set_interval(cls, interval):
        return interval or "month"

    @validator("weather_condition", pre=True, always=True)
    def set_weather_condition(cls, weather_condition):
        return weather_condition or "both"

    @root_validator
    def check_date_order(cls, values):
        assert values["start_date"] < values["end_date"], (
            f"ERROR: start: {values['start_date']} -> end: {values['end_date']}  "
            "You must not end before you've even begun."
        )
        return values


class TimeseriesSchema(TimeseriesBaseSchema):
    variable: str = Field(
        ...,
        regex="|".join([s + "$" for s in cfg["variables"].keys()]),
        example="discharge",
    )
    site: str = Field(..., example="ALISO_JERONIMO")
    trace_upstream: Optional[bool] = True
    aggregation_method: Optional[AggregationMethod] = Field(None, example="mean")
    nearest_rainfall_station: Optional[str] = Field(None, example="ALISO_JERONIMO")

    @validator("site")
    def check_site(cls, v):

        # load_file will cache this so it doesn't happen for frequent requests
        site_props = [
            f["properties"] for f in json.loads(load_file(cfg["site_path"]))["features"]
        ]
        valid_sites = [d["station"] for d in site_props]
        assert v in valid_sites, f"'{v}' is not valid. \n\tOptions are: {valid_sites}"

        return v

    @validator("variable")
    def check_variable(cls, v):
        valid_variables = list(cfg["variables"].keys())

        assert (
            v in valid_variables
        ), f"invalid variable: `{v}`. \n\tOptions are: {valid_variables}"
        return v

    @validator("trace_upstream", pre=True, always=True)
    def set_trace_upstream(cls, trace_upstream):
        if trace_upstream is None:
            return True
        return trace_upstream

    @validator("nearest_rainfall_station", pre=True, always=True)
    def set_nearest_rainfall_station(cls, nearest_rainfall_station):
        if nearest_rainfall_station is not None:
            cls.check_site(nearest_rainfall_station)
        return nearest_rainfall_station

    @root_validator
    def check_nearest_rainfall_station_if_provided(cls, values):
        nearest_station = values.get("nearest_rainfall_station")

        if nearest_station is not None:

            site_props = [
                f["properties"]
                for f in json.loads(load_file(cfg["site_path"]))["features"]
            ]

            nearest_site_info: Dict = next(
                (x for x in site_props if x["station"] == nearest_station), {}
            )
            assert nearest_site_info.get(
                f"has_rainfall"
            ), f"'rainfall' not found at site {nearest_station!r}."

        return values

    @root_validator
    def check_site_variable(cls, values):
        site = values.get("site", r"¯\_(ツ)_/¯")
        variable = values.get("variable", r"¯\_(ツ)_/¯")
        source = cfg.get("variables", {}).get(variable, {}).get("source")
        nearest_station = values.get("nearest_rainfall_station")

        # load_file will cache this so it doesn't happen for frequent requests
        site_props = [
            f["properties"] for f in json.loads(load_file(cfg["site_path"]))["features"]
        ]
        site_info: Dict = next((x for x in site_props if x["station"] == site), {})

        # we only need to validate that the variable is available for hydstra
        # variables. Dt_metric variables are always available.
        if source == "hydstra":

            if variable == "rainfall" and not site_info.get(f"has_{variable}"):
                nearest_station = (
                    values.get("nearest_rainfall_station")
                    or site_info["nearest_rainfall_station"]
                )

                warnings = values.get("warnings", [])
                warnings.append(
                    f"Warning: variable {variable!r} not available for site {site!r}. "
                    f"Overriding to nearest site {nearest_station!r}"
                )
                values["warnings"] = warnings
                values["site"] = nearest_station

                return values

            assert site_info.get(
                f"has_{variable}"
            ), f"{variable!r} not found at site {site!r}."

        return values

    @root_validator
    def check_aggregation_method(cls, values):

        variable = values.get("variable", r"¯\_(ツ)_/¯")
        agg = values.get("aggregation_method", r"¯\_(ツ)_/¯")

        allowed_aggs = (
            cfg.get("variables", {}).get(variable, {}).get("allowed_aggregations", [])
        )

        assert len(allowed_aggs) >= 1, f"no data for {variable}."

        if not agg in allowed_aggs:
            default_agg = allowed_aggs[0]

            warnings = values.get("warnings", [])
            warnings.append(
                f"Warning: Aggregation method '{agg}' not allowed for variable '{variable}'. "
                f"Options are: {allowed_aggs}. "
                f"Overriding to: {default_agg}."
            )
            values["aggregation_method"] = default_agg
            values["warnings"] = warnings

        return values

    @root_validator
    def check_dt_metric_dates(cls, values):
        variable = values.get("variable", r"¯\_(ツ)_/¯")
        source = cfg.get("variables", {}).get(variable, {}).get("source")

        if source == "dt_metrics":

            if values["interval"] == "month":
                assert (
                    values["start_date"][-2:] == "01"
                ), "Drool Tool monthly intervals must start on the first of the month."

            if values["interval"] == "year":
                assert (
                    values["start_date"][-5:] == "01-01"
                ), "Drool Tool yearly intervals must start on the first of the year."

        return values

    @root_validator
    def check_dt_metric_weather_condition(cls, values):
        variable = values.get("variable", r"¯\_(ツ)_/¯")
        source = cfg.get("variables", {}).get(variable, {}).get("source")
        weather_condition = values.get("weather_condition", "both")

        if source == "dt_metrics" and weather_condition != "both":
            warnings = values.get("warnings", [])
            warnings.append(
                f"Warning: `weather_condition` option is ignored for DT Metrics."
            )
            values["warnings"] = warnings

        return values


class ListTimeseriesSchema(BaseModel):
    timeseries: List[TimeseriesSchema]

    @validator("timeseries", pre=True, always=True)
    def check_timeseries(cls, v):
        if isinstance(v, str):
            return orjson.loads(v)
        return v


class MultiVarSchema(ListTimeseriesSchema):
    @root_validator(pre=True)
    def broadcast_all(cls, values):
        timeseries = values.get("timeseries", [])
        if isinstance(timeseries, str):
            timeseries = orjson.loads(timeseries)
            values["timeseries"] = timeseries
        other_vars = [k for k in values if k != "timeseries"]

        for ts in timeseries:
            for v in other_vars:
                b_v = values.get(v, None)
                if b_v is not None:
                    ts[v] = b_v
        return values


class RegressionSchema(MultiVarSchema):
    regression_method: Optional[RegressionMethod] = None

    @validator("regression_method", pre=True, always=True)
    def check_method(cls, method):

        if method is None:
            return "linear"

        return method

    @validator("timeseries", pre=True, always=True)
    def check_len_timeseries(cls, timeseries):
        assert (
            len(timeseries) == 2
        ), f"two (2) timeseries are required but {len(timeseries)} were sent."
        return timeseries

    @root_validator
    def check_interval(cls, values):
        timeseries = values.get("timeseries")
        sources = []
        intervals = []

        for ts in timeseries:
            sources.append(cfg.get("variables", {}).get(ts.variable, {}).get("source"))
            intervals.append(ts.interval)

        assert all(
            i == intervals[0] for i in intervals
        ), f"invervals must be the same for both timeseries. '{intervals[0]}' != '{intervals[1]}'"

        if "dt_metrics" in sources:
            assert all(
                ts.interval in ["month", "year"] for ts in timeseries
            ), f"inverval must be 'month' or 'year' for drool tool metrics."

        return values


class DiversionScenarioSchema(BaseModel):
    site: str
    start_date: str
    end_date: str
    diversion_rate_cfs: float
    storage_max_depth_ft: Optional[float] = 0.0
    storage_initial_depth_ft: Optional[float] = 0.0
    storage_area_sqft: Optional[float] = 0.0
    infiltration_rate_inhr: Optional[float] = 0.0
    rainfall_event_depth_threshold: Optional[float] = 0.1
    event_separation_hrs: Optional[float] = 6.0
    after_rain_delay_hrs: Optional[float] = 72.0
    diversion_months_active: Optional[List[int]] = None
    diversion_days_active: Optional[List[int]] = None
    diversion_hours_active: Optional[List[int]] = None
    operated_weather_condition: Optional[Weather] = None
    nearest_rainfall_station: Optional[str] = None

    @validator("operated_weather_condition", pre=True, always=True)
    def set_operated_weather_condition(cls, operated_weather_condition):
        return operated_weather_condition or "dry"

    @root_validator
    def check_site(cls, values):
        ts = TimeseriesSchema(
            site=values.get("site"),
            start_date=values.get("start_date"),
            end_date=values.get("end_date"),
            nearest_rainfall_station=values.get("nearest_rainfall_station"),
            weather_condition=Weather.both,  # we are initializing discharge timeseries here, not the diversion behavior
            variable="discharge",
            aggregation_method=AggregationMethod.mean,
            interval=Interval.hour,
        )

        values["ts"] = ts.dict()

        return values
