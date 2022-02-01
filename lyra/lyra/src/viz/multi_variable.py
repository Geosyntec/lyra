import asyncio
from typing import Any, Dict, List

import altair as alt
import pandas

from lyra.core.config import cfg
from lyra.src.timeseries import Timeseries, gather_timeseries, utils


def make_source_json(source: pandas.DataFrame) -> List[Dict[str, Any]]:
    # source = source.reindex(columns=["date", "value", "label"])
    result: List[Dict[str, Any]] = source.to_dict(orient="records")
    return result


def make_source_csv(source: pandas.DataFrame) -> str:
    csv = (
        source.reindex(columns=["date", "label", "value"])
        .pivot(index="date", columns="label", values="value")
        .reset_index()
        .to_csv(index=False)
    )

    return csv


def multi_var_ts_label(t: Timeseries) -> str:
    is_dt_metric = t.variable_info["source"] == "dt_metrics"

    _site = t.site
    _var_name = t.variable_info["name"]
    _var_units = t.variable_info["units"]
    _us = "Upstream from" if t.trace_upstream and is_dt_metric else "from"
    _method = t.aggregation_method.title() if t.aggregation_method else ""
    _interval = t.interval
    _weather_condition = (
        f"{t.weather_condition.title()} Weather "
        if t.weather_condition != "both"
        else ""
    )

    return f"{_method} 1 {_interval} {_weather_condition}{_var_name} ({_var_units}) {_us} {_site}"


def make_timeseries(timeseries: List[Dict[str, Any]], **kwargs: Any,) -> List[Any]:

    ts = []
    for dct in timeseries:
        t = Timeseries(**dct)
        ts.append(t)

    asyncio.run(gather_timeseries(ts))

    return ts


def make_source(ts: List[Timeseries]) -> pandas.DataFrame:
    for t in ts:
        t.label = multi_var_ts_label(t)
    dfs = [t.timeseries_src.assign(label=t.label).reset_index() for t in ts]
    df = pandas.concat(dfs)
    return df


def make_plot(source: pandas.DataFrame) -> alt.TopLevelMixin:

    source = source.rename(columns={"date": "Date"})  # for display purposes

    vstack = []
    height = 300
    width = 400
    variables = source.variable.unique()
    if len(variables) > 1:
        height = 150

    legend_selection = alt.selection_multi(fields=["label"], bind="legend")

    for var in variables:

        data = source.query("variable==@var").pipe(
            utils.drop_runs_tidy, groupby=["label"], date_col="Date"
        )
        var_info = cfg.get("variables", {}).get(var)

        interpolate = alt.Undefined

        if var == "rainfall":
            interpolate = "step-after"

        base = alt.Chart(data).encode(x="Date:T")

        line = (
            base.mark_line(interpolate=interpolate)
            .encode(
                y=alt.Y(
                    "value:Q",
                    title=f"{var_info['name']} ({var_info['units']})",
                    scale=alt.Scale(domain=(0, data["value"].max() * 1.1)),
                ),
                color=alt.Color("label:N", sort=variables),
                opacity=alt.condition(legend_selection, alt.value(0.8), alt.value(0.2)),
            )
            .properties(height=height, width=width)
        )

        nearest = alt.selection_single(
            nearest=True,
            on="mouseover",
            fields=["Date"],
            empty="none",
            clear="mouseout",
        )

        # Draw points on the line, and highlight based on selection
        points = (
            line.mark_point().transform_filter(nearest).encode(opacity=alt.value(1))
        )

        # Draw text labels near the points, and highlight based on selection
        ymax = data["value"].max()
        if ymax < 1:
            num_fmt = ",.3f"
        elif ymax < 100:
            num_fmt = ",.1f"
        else:
            num_fmt = ",.0f"
        text = (
            line.mark_text(align="right", dx=-7, dy=-7, fontStyle="bold")
            .transform_filter(nearest)
            .encode(text=alt.Text("value:Q", format=num_fmt), opacity=alt.value(1))
        )

        # Draw a rule at the location of the selection
        rule = (
            base.mark_rule()
            .encode(
                opacity=alt.condition(nearest, alt.value(0.3), alt.value(0)),
                tooltip=[alt.Tooltip("Date", format="%b %-d, %Y@%H:%M"),],
            )
            .add_selection(nearest)
        )

        chart: alt.LayerChart = alt.layer(line, points, rule, text).add_selection(
            legend_selection
        )

        vstack.append(chart)

    return (
        alt.vconcat(*vstack)
        .resolve_scale(
            color="independent",  # color=independant will separate the legends
            x="shared",
        )
        .configure_legend(labelLimit=0, orient="top", direction="vertical", title=None)
    )
