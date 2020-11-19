from typing import Any, Dict, List, Optional, Union

import altair as alt
import pandas

from lyra.src.timeseries import Timeseries


def expand_list(l: Optional[List[Any]], n: int, default: Any) -> List[Any]:
    if l is None:
        return [default] * n

    while len(l) < n:
        l.append(l[-1])
    return l


def dispatch(**kwargs: Any) -> alt.TopLevelMixin:
    source = make_source(**kwargs)
    chart = make_plot(source.reindex(columns=["date", "value", "label"]))
    return chart


def make_source(
    variable: str,
    sites: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    intervals: Optional[List[str]] = None,
    trace_upstreams: Optional[List[bool]] = None,
    agg_methods: Optional[List[str]] = None,
    **kwargs: Any,
) -> pandas.DataFrame:

    if start_date is None:
        start_date = "2010-01-01"
    if end_date is None:
        end_date = "2020-01-01"

    n = len(sites)

    intervals = expand_list(intervals, n, "month")
    agg_methods = expand_list(agg_methods, n, "mean")
    trace_upstreams = expand_list(trace_upstreams, n, False)

    ts = []

    for site, interval, agg_method, trace_upstream in zip(
        sites, intervals, agg_methods, trace_upstreams
    ):

        t = Timeseries(
            site=site,
            variable=variable,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            agg_method=agg_method,
            trace_upstream=trace_upstream,
        )

        is_dt_metric = t.variable_info["source"] == "dt_metrics"

        _site = t.site.replace("_", " ").title()
        _var_name = t.variable_info["name"]
        _var_units = t.variable_info["units"]
        _us = "Upstream from" if trace_upstream and is_dt_metric else "from"
        _method = agg_method.title() if agg_method else ""

        label = f"{_method} {_var_name} ({_var_units}/{interval}) {_us} {_site}"

        _ts = t.timeseries_src.assign(label=label).reset_index()

        ts.append(_ts)

    source = pandas.concat(ts)

    return source


def make_source_json(source: pandas.DataFrame) -> List[Dict[str, Any]]:
    source = source.reindex(columns=["date", "value", "label"])
    result: List[Dict[str, Any]] = source.to_dict(orient="records")
    return result


def make_source_csv(source: pandas.DataFrame) -> str:
    site = ",".join(source["site"].unique())
    variable = ",".join(source["variable"].unique())
    csv = (
        source.reindex(columns=["date", "label", "value"])
        .pivot(index="date", columns="label", values="value")
        .reset_index()
        .to_csv(index=False)
    )

    pkg = "\n".join([site, variable, csv])

    return pkg


def make_plot(source: Union[str, pandas.DataFrame]) -> alt.TopLevelMixin:

    line = (
        alt.Chart(source).mark_line().encode(x="date:T", y="value:Q", color="label:N")
    )

    nearest = alt.selection(
        type="single", nearest=True, on="mouseover", fields=["date"], empty="none"
    )

    selectors = (
        alt.Chart(source)
        .mark_point()
        .encode(x="date:T", y="value:Q", opacity=alt.value(0),)
        .add_selection(nearest)
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align="left", dx=5, dy=-5).encode(
        text=alt.condition(nearest, "value:Q", alt.value(" "))
    )

    # Draw a rule at the location of the selection
    rules = (
        alt.Chart(source)
        .mark_rule(color="gray")
        .encode(x="date:T",)
        .transform_filter(nearest)
    )

    chart: alt.LayerChart = alt.layer(line, selectors, points, rules, text)

    return chart
