import asyncio

import pandas

from lyra.core.config import config
from lyra.src.hydstra import helper
from lyra.src.mnwd.helper import get_timeseries_from_dt_metrics


class Timeseries(object):
    def __init__(
        self,
        site: str,
        variable: str,
        interval: str = "day",
        agg_method: str = "mean",
        trace_upstream: bool = False,
        start_date: str = None,  # "yyyy-mm-dd"
        end_date: str = None,
        **kwargs,
    ) -> None:
        self.site = site
        self.variable = variable
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval
        self.agg_method = agg_method
        self.trace_upstream = trace_upstream

        self.cfg = config()

        self.variable_info = self.cfg["variables"].get(variable)
        self.kwargs = kwargs

        # properties
        self._timeseries = None
        self._timeseries_src = None

    @property
    def timeseries(self) -> pandas.Series:
        if self._timeseries is None:  # pragma: no branch
            self._timeseries = self.init_ts()
        return self._timeseries

    @property
    def timeseries_src(self) -> pandas.DataFrame:
        if self._timeseries_src is None:  # pragma: no branch
            self._timeseries_src = (
                self.timeseries.to_frame()
                .assign(site=self.site)
                .assign(variable=self.variable)
                # .assign(variable_name=self.variable_info["name"])
                # .assign(variable_units=self.variable_info["units"])
            )
        return self._timeseries_src

    def _init_hydstra(self):
        site_preferred_variables = self.cfg["preferred_variables"]
        varfrom = site_preferred_variables[self.site][self.variable]["varfrom"]
        varto = site_preferred_variables[self.site][self.variable].get("varto")

        timeseries_details = asyncio.run(
            helper.get_site_variable_as_trace(
                site=self.site,
                varfrom=varfrom,
                varto=varto,
                start_date=self.start_date,
                end_date=self.end_date,
                interval=self.interval,
                agg_method=self.agg_method,
                **self.kwargs,
            )
        )

        trace = timeseries_details["trace"]

        timeseries = helper.hydstra_trace_to_series(trace)

        return timeseries

    def _init_dt_metrics(self):
        variable = self.cfg["variables"][self.variable]["variable"]
        timeseries = get_timeseries_from_dt_metrics(
            variable,
            site=self.site,
            start_date=self.start_date,
            end_date=self.end_date,
            agg_method=self.agg_method,
            trace_upstream=self.trace_upstream,
            **self.kwargs,
        )
        return timeseries

    def init_ts(self) -> None:
        source = self.variable_info.get("source")

        if source == "hydstra":
            ts = self._init_hydstra()

        elif source == "dt_metrics":
            ts = self._init_dt_metrics()

        else:  # pragma: no cover
            raise ValueError(
                f"no method for loading from source: {source}. See config file."
            )

        return ts
