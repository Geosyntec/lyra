import asyncio
import datetime
import json
from functools import partial
from typing import Any, Dict, List, Optional

import pandas
import pytz

from lyra.core.config import cfg
from lyra.core.errors import HydstraIOError
from lyra.core.io import load_file
from lyra.core.utils import local_path
from lyra.src.hydstra import helper
from lyra.src.mnwd.helper import get_timeseries_from_dt_metrics

AGG_REMAP = {
    # hydstra : pandas
    "tot": "sum",
    "cum": "cumsum",
}

SWN_SITES_PATH = local_path("data/mount/swn/hydstra").resolve() / "swn_sites.json"


class Timeseries(object):
    def __init__(
        self,
        site: str,
        variable: str,
        aggregation_method: str,
        interval: str = "day",
        start_date: str = None,  # "yyyy-mm-dd"
        end_date: str = None,
        trace_upstream: bool = True,
        hydstra_kwargs: Optional[Dict] = None,
        warnings: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> None:
        self.site = site
        self.variable = variable
        self.start_date = start_date or "2020-01-01"
        self.end_date = (
            end_date
            or datetime.datetime.now(pytz.timezone("US/Pacific")).date().isoformat()
        )
        self.interval = interval
        self.aggregation_method = aggregation_method
        self.trace_upstream = trace_upstream
        self.cfg = cfg
        self.variable_info = self.cfg["variables"].get(self.variable, {})
        allowed_aggs = self.variable_info["allowed_aggregations"]
        self.aggregation_method = (
            aggregation_method
            if aggregation_method in allowed_aggs
            else allowed_aggs[0]
        )
        self.warnings = warnings or []

        # load_file will cache this so it doesn't happen for frequent requests
        all_props: List[Any] = [
            f["properties"]
            for f in json.loads(load_file(self.cfg["site_path"]))["features"]
        ]

        self.site_props: Dict[str, Any] = next(
            (x for x in all_props if x["station"] == site), {}
        )

        self.hydstra_kwargs: Dict[str, Any] = hydstra_kwargs or {}
        self.kwargs: Dict[str, Any] = kwargs

        # properties
        self._timeseries = None
        self._timeseries_src = None
        self.label = self.__repr__()

    def __repr__(self):

        is_dt_metric = self.variable_info["source"] == "dt_metrics"
        _var_name = self.variable_info["name"]
        _var_units = self.variable_info["units"]
        _us = "Upstream from" if self.trace_upstream and is_dt_metric else "from"
        _method = self.aggregation_method.title() if self.aggregation_method else ""

        repr = (
            f"{_method} 1 {self.interval} {_var_name} ({_var_units}) {_us} "
            f"{self.site} from {self.start_date} to {self.end_date}"
        )

        return repr

    @property
    def timeseries(self) -> pandas.Series:
        if self._timeseries is None:  # pragma: no branch
            asyncio.run(self.init_ts())
        return self._timeseries

    @timeseries.setter
    def timeseries(self, timeseries):
        self._timeseries = timeseries

    @property
    def timeseries_src(self) -> pandas.DataFrame:
        if self._timeseries_src is None:  # pragma: no branch
            self._timeseries_src = self.timeseries.assign(site=self.site).assign(
                variable=self.variable
            )
        return self._timeseries_src

    async def _init_hydstra(self) -> pandas.Series:
        hyd_variable_info: Dict[str, Any] = self.site_props.get(
            self.variable + "_info", {}
        )

        inputs = dict(
            site=self.site,
            varfrom=hyd_variable_info["varfrom"],
            varto=hyd_variable_info["varto"],
            start_date=self.start_date,
            end_date=self.end_date,
            interval=self.interval,
            agg_method=self.aggregation_method,
            **self.hydstra_kwargs,
        )

        timeseries_details = await helper.get_site_variable_as_trace(**inputs)

        if "error_msg" in timeseries_details.keys():
            num = timeseries_details["error_num"]
            if num == 220:
                raise HydstraIOError(f"{timeseries_details['error_msg']}", data=inputs)

        if not timeseries_details.get("trace"):
            inputs["varfrom"] = hyd_variable_info["varfrom_fallback"]
            self.warnings.append(
                f"Warning: variable '{hyd_variable_info['varfrom']}' not available. "
                f"Falling back to '{hyd_variable_info['varfrom_fallback']}'"
            )

            timeseries_details = await helper.get_site_variable_as_trace(**inputs)

        trace = timeseries_details.get("trace")

        if not trace:  # pragma: no cover
            raise ValueError(f"inputs failed: {inputs}")

        return helper.hydstra_trace_to_series(trace)

    async def _init_dt_metrics(self) -> pandas.Series:
        variable = self.variable_info["variable"]
        catchidn = self.site_props["CatchIDN"]
        self.aggregation_method = "tot"
        self.interval = (
            "month" if self.interval not in ["year", "month"] else self.interval
        )

        inputs = dict(
            variable=variable,
            site=catchidn,
            start_date=self.start_date,
            end_date=self.end_date,
            agg_method=AGG_REMAP[self.aggregation_method],
            trace_upstream=self.trace_upstream,
            interval=self.interval,
            **self.kwargs,
        )

        loop = asyncio.get_running_loop()
        f = partial(get_timeseries_from_dt_metrics, **inputs)

        timeseries = await loop.run_in_executor(None, f)

        return timeseries

    async def init_ts(self, delay: Optional[float] = None) -> pandas.Series:
        source = self.variable_info.get("source")

        if source == "hydstra":
            if delay:
                # need to rate limit hydstra to 1 request per second, unfortunately.
                # this issue was reported to Hydstra support on 2021-07-12.
                # per communication 20201-07-19 this issue has been resolved.
                await asyncio.sleep(delay)

            self.timeseries = await self._init_hydstra()

        elif source == "dt_metrics":
            self.timeseries = await self._init_dt_metrics()

        else:  # pragma: no cover
            raise NotImplementedError(
                f"no method for loading {self.variable} from source: {source}. See config file."
            )


async def gather_timeseries(ts):

    await asyncio.gather(*(t.init_ts(delay=0) for i, t in enumerate(ts)))
