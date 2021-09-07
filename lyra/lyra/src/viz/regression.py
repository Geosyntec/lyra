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
            format(datum.coef[0],".2f") + " + " + \
            format(datum.coef[1],".2f") + "x" \
            ',
        ),
    },
    "quad": {
        "calculate": dict(
            rSquared='format(datum.rSquared,".2f")',
            equation='\
            "y = "+\
            format(datum.coef[0],".2f") + " + " + \
            format(datum.coef[1],".2f") + "x + " + \
            format(datum.coef[2],".2f") + "x\u00B2" \
            ',
        ),
    },
    "poly": {
        "calculate": dict(
            rSquared='format(datum.rSquared,".2f")',
            equation='\
            "y = "+\
            format(datum.coef[0],".2f") + " + " + \
            format(datum.coef[1],".2f") + "x + " + \
            format(datum.coef[2],".2f") + "x\u00B2" + \
            format(datum.coef[3],".2f") + "x\u00B3" \
            ',
        ),
    },
    "exp": {
        "calculate": dict(
            rSquared='format(datum.rSquared,".2f")',
            equation='\
            "y = "+\
            format(datum.coef[0],".2f") + " * e^(" + \
            format(datum.coef[1],".2f") + " * x)" \
            ',
        ),
    },
    "pow": {
        "calculate": dict(
            rSquared='format(datum.rSquared,".2f")',
            equation='\
            "y = "+\
            format(datum.coef[0],".2f") + " * x^" + \
            format(datum.coef[1],".2f") \
            ',
        ),
    },
    "log": {
        "calculate": dict(
            rSquared='format(datum.rSquared,".2f")',
            equation='\
            "y = "+\
            format(datum.coef[0],".2f") + " * " + \
            format(datum.coef[1],".2f") + "x" \
            ',
        ),
    },
}


def make_source_json(source: pandas.DataFrame) -> List[Dict[str, Any]]:
    # source = source.reindex(columns=["date", "value", "label"])
    result: List[Dict[str, Any]] = source.reset_index().to_dict(orient="records")
    return result


def make_source_csv(source: pandas.DataFrame) -> str:
    # site = ",".join(source["site"].unique())
    # variable = ",".join(source["variable"].unique())
    # csv = (
    #     source.reindex(columns=["date", "label", "value"])
    #     .pivot(index="date", columns="label", values="value")
    #     .reset_index()
    #     .to_csv(index=False)
    # )

    # pkg = "\n".join([site, variable, csv])

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
    x = tx.timeseries_src.assign(
        outlier_x=lambda df: numpy.abs(zscore(df["value"])) > 6
    ).rename(columns={"value": tx.label})
    y = ty.timeseries_src.assign(
        outlier_y=lambda df: numpy.abs(zscore(df["value"])) > 6
    ).rename(columns={"value": ty.label})
    source = (
        pandas.concat([x, y], axis=1)
        .dropna()
        .assign(
            label=lambda df: numpy.where(
                df["outlier_x"] | df["outlier_y"], "outlier (zscore > 6)", "data"
            )
        )
    )[[tx.label, ty.label, "label"]]

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

    chart = (
        alt.Chart(source.query('label=="data"'), width=width, height=height)
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
            color="label:N",
            opacity=alt.value(0.5),
        )
    )

    outlier = (
        alt.Chart(source.query('label!="data"'))
        .mark_point(filled=True)
        .encode(x="x:Q", y="y:Q", color="label:N", opacity=alt.value(0.8))
    )

    line = (
        chart.transform_regression(on="x", regression="y", method=method)
        .mark_line(clip=True,)
        .encode(color=alt.value("firebrick"), opacity=alt.value(1))
    )

    regression = chart.transform_regression(
        "x", "y", method=method, params=True
    ).transform_calculate(**HOWS[method]["calculate"])

    params = []
    yoff = chart.height + 60
    xoff = chart.width / 2
    for label, val in [("R\u00B2:", "rSquared"), ("equation: ", "equation")]:
        p = regression.mark_text(align="right", text=label).encode(
            x=alt.value(xoff),
            y=alt.value(yoff),  # pixels from left  # pixels from top
            opacity=alt.value(1),
            color=alt.value("black"),
        )
        params.append(p)

        p = regression.mark_text(align="left", lineBreak="\n").encode(
            x=alt.value(xoff + 4),  # pixels from left
            y=alt.value(yoff),  # pixels from top
            text=f"{val}:N",
            opacity=alt.value(1),
            color=alt.value("black"),
        )
        params.append(p)

        yoff += 15

    full_chart = ((chart + outlier + line) + alt.layer(*params)).configure_legend(
        labelLimit=0, orient="top", direction="vertical", title=None
    )

    return full_chart
