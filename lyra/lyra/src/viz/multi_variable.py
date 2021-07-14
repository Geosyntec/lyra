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


def multi_var_ts_label(t: Timeseries) -> str:
    is_dt_metric = t.variable_info["source"] == "dt_metrics"

    _site = t.site
    _var_name = t.variable_info["name"]
    _var_units = t.variable_info["units"]
    _us = "Upstream from" if t.trace_upstream and is_dt_metric else "from"
    _method = t.aggregation_method.title() if t.aggregation_method else ""
    _interval = t.interval

    return f"{_method} 1 {_interval} {_var_name} ({_var_units}) {_us} {_site}"


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

    vstack = []
    height = 300
    variables = source.variable.unique()
    if len(variables) > 1:
        height = 150

    legend_selection = alt.selection_multi(fields=["label"], bind="legend")

    for var in variables:

        data = source.query("variable==@var").pipe(
            utils.drop_runs_tidy, groupby=["label"]
        )
        var_info = cfg.get("variables", {}).get(var)

        line = (
            alt.Chart(data)
            .mark_line()
            .encode(
                x="date:T",
                y=alt.Y(
                    "value:Q",
                    title=f"{var_info['name']} ({var_info['units']})",
                    scale=alt.Scale(domain=(0, data["value"].max() * 1.05)),
                ),
                color=alt.Color("label:N", sort=variables),
                opacity=alt.condition(legend_selection, alt.value(1), alt.value(0.2)),
            )
            .properties(height=height)
        )

        nearest = alt.selection(
            type="single", nearest=True, on="mouseover", fields=["date"], empty="none"
        )

        selectors = (
            alt.Chart(data)
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
            text=alt.condition(nearest, "value:Q", alt.value(" "), format=",.1f")
        )

        # Draw a rule at the location of the selection
        rules = (
            alt.Chart(data)
            .mark_rule(color="gray")
            .encode(x="date:T",)
            .transform_filter(nearest)
        )

        chart: alt.LayerChart = alt.layer(
            line, selectors, points, rules, text,
        ).add_selection(legend_selection)

        vstack.append(chart)

    return (
        alt.vconcat(*vstack)
        .resolve_scale(
            color="independent",  # color=independant will separate the legends
            x="shared",
        )
        .configure_legend(labelLimit=0)
    )
