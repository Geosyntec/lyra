import asyncio
from typing import Any, Dict, List, Optional

import altair as alt
import numpy
import pandas
from scipy.stats import zscore

from lyra.src.timeseries import Timeseries, gather_timeseries

HOWS = {
    "linear": {
        "calculate": dict(
            rSquared='format(datum.rSquared,".2f")',
            equation='\
            "y = "+\
            format(datum.coef[0],".4f") + " + " + \
            format(datum.coef[1],".4f") + "x" \
            ',
        ),
    },
    "quad": {
        "calculate": dict(
            rSquared='format(datum.rSquared,".2f")',
            equation='\
            "y = "+\
            format(datum.coef[0],".4f") + " + " + \
            format(datum.coef[1],".4f") + "x + " + \
            format(datum.coef[2],".4f") + "x\u00B2" \
            ',
        ),
    },
    "poly": {
        "calculate": dict(
            rSquared='format(datum.rSquared,".2f")',
            equation='\
            "y = "+\
            format(datum.coef[0],".4f") + " + " + \
            format(datum.coef[1],".4f") + "x + " + \
            format(datum.coef[2],".4f") + "x\u00B2" + \
            format(datum.coef[3],".4f") + "x\u00B3" \
            ',
        ),
    },
    "exp": {
        "calculate": dict(
            rSquared='format(datum.rSquared,".2f")',
            equation='\
            "y = "+\
            format(datum.coef[0],".4f") + " * e^(" + \
            format(datum.coef[1],".4f") + " * x)" \
            ',
        ),
    },
    "pow": {
        "calculate": dict(
            rSquared='format(datum.rSquared,".2f")',
            equation='\
            "y = "+\
            format(datum.coef[0],".4f") + " * x^" + \
            format(datum.coef[1],".4f") \
            ',
        ),
    },
    "log": {
        "calculate": dict(
            rSquared='format(datum.rSquared,".2f")',
            equation='\
            "y = "+\
            format(datum.coef[0],".4f") + " * " + \
            format(datum.coef[1],".4f") + "x" \
            ',
        ),
    },
}


def make_source_json(source: pandas.DataFrame) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = source.reset_index().to_dict(orient="records")
    return result


def make_source_csv(source: pandas.DataFrame) -> str:

    return source.reset_index().to_csv(index=False)


def split_keep_delim(string, delim):

    ls = string.split(delim)
    return [e + delim for e in ls[:-1]] + [ls[-1]]


def regression_ts_label(t: Timeseries) -> str:
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


def make_source(ts: List[Timeseries], method: Optional[str] = None) -> pandas.DataFrame:

    tx, ty, *_ = ts
    for t in [tx, ty]:
        t.label = regression_ts_label(t)
    if tx.label == ty.label:
        for t, tag in zip([tx, ty], [" (x)", " (y)"]):
            t.label += tag

    x = tx.timeseries_src.rename(columns={"value": tx.label})
    y = ty.timeseries_src.rename(columns={"value": ty.label})

    source = (
        pandas.concat([x, y], axis=1)
        .dropna()
        .assign(label="Data")[[tx.label, ty.label, "label"]]
    )

    if method in ["log", "pow", "exp"]:
        source = source.loc[~(source <= 0).any(axis=1)]
    return source


def make_plot(
    source: pandas.DataFrame, method: Optional[str] = None
) -> alt.TopLevelMixin:
    if method is None:
        method = "linear"

    x_label, y_label, *_ = source.columns
    source.columns = ["x", "y", "label"]
    width = 400
    height = 400

    source = source.assign(tooltip="")

    if not source.empty:
        source = source.assign(
            tooltip=lambda df: (
                df["x"].round(2).apply(str) + ", " + df["y"].round(2).apply(str)
            )
        )

    nearest = alt.selection_single(on="mouseover", empty="none")

    points = (
        alt.Chart(source)
        .properties(height=height, width=width)
        .mark_point(filled=True)
        .encode(
            x=alt.X(
                "x:Q",
                title=split_keep_delim(x_label, ")"),
                scale=alt.Scale(domain=(0, source["x"].max() * 1.05)),
            ),
            y=alt.Y(
                "y:Q",
                title=split_keep_delim(y_label, ")"),
                scale=alt.Scale(domain=(0, source["y"].max() * 1.05)),
            ),
            color=alt.condition(nearest, alt.value("orange"), "label:N",),
            opacity=alt.condition(nearest, alt.value(0.9), alt.value(0.5),),
            size=alt.condition(nearest, alt.value(150), alt.value(75)),
            tooltip="tooltip",
        )
    )

    line = (
        alt.Chart(source)
        .transform_regression(on="x", regression="y", method=method)
        .mark_line(clip=True,)
        .encode(x="x:Q", y="y:Q", color=alt.value("firebrick"), opacity=alt.value(1))
    )

    regression = (
        alt.Chart(source)
        .transform_regression("x", "y", method=method, params=True)
        .transform_calculate(**HOWS[method]["calculate"])
    )

    params = []
    yoff = height + 60
    xoff = width / 8
    for label, val in [("R\u00B2:", "rSquared"), ("Equation: ", "equation")]:
        p = regression.mark_text(align="right", text=label, clip=False).encode(
            x=alt.value(xoff),
            y=alt.value(yoff),  # pixels from left  # pixels from top
            opacity=alt.value(1),
            color=alt.value("black"),
        )
        params.append(p)

        p = regression.mark_text(align="left", lineBreak="\n", clip=False).encode(
            x=alt.value(xoff + 4),  # pixels from left
            y=alt.value(yoff),  # pixels from top
            text=f"{val}:N",
            opacity=alt.value(1),
            color=alt.value("black"),
        )
        params.append(p)

        yoff += 15

    chart = points.add_selection(nearest) + line
    annotation = alt.layer(*params)

    full_chart = (
        (chart + annotation)
        .configure_legend(labelLimit=0, orient="top", direction="vertical", title=None)
        .interactive()
    )

    return full_chart
