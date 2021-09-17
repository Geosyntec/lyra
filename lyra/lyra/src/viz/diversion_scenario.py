from typing import Any, Dict, List

import altair as alt
import numpy
import pandas

from lyra.src.diversion import simulate_diversion
from lyra.src.timeseries import utils


def make_source_json(source: pandas.DataFrame) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = source.to_dict(orient="records")
    return result


def make_source_csv(source: pandas.DataFrame) -> str:

    csv = (
        source.reindex(columns=["date", "variable", "value"])
        .pivot(index="date", columns="variable", values="value")
        .reset_index()
        .to_csv(index=False)
    )

    pkg = "\n".join([csv])

    return pkg


def make_source(**kwargs: Dict) -> pandas.DataFrame:
    df = simulate_diversion(**kwargs).reset_index().melt(id_vars="date")  # type: ignore
    return df


def make_summary_table(df):
    table = {
        "column_names": None,
        "records": [],
    }
    inflow_vol = df.query('variable == "inflow_volume"')["value"].sum()
    diversion_vol = df.query('variable == "diverted_volume"')["value"].sum()
    diverted_pct = diversion_vol / inflow_vol * 100

    records = [
        {
            "label": "Total Inflow Volume (cuft)",
            "units": "cuft",
            "value": float(numpy.round(inflow_vol, 2)),
            "description": f"Total volume entering the diversion during the scenario.",
        },
        {
            "label": "Total Diverted Volume (cuft)",
            "units": "cuft",
            "value": float(numpy.round(diversion_vol, 2)),
            "description": f"Total volume diverted during this scenario.",
        },
        {
            "label": r"% of Inflow Diverted",
            "units": "%",
            "value": float(numpy.round(diverted_pct, 1)),
            "description": f"Diverted volume as percentage of inflow volume.",
        },
    ]

    table["records"] = records

    return table


def make_layer(
    source, fields, xlim=None, ylim=None, text_sigfigs=3, ylabel=None, interpolate=None,
):

    if interpolate is None:
        interpolate = alt.Undefined
    nearest = alt.selection(
        type="single", nearest=True, on="mouseover", fields=["date"], empty="none"
    )

    title_fields = {s: s.title().replace("_", " ") for s in fields}

    plot_src = (
        source.query("variable in @fields")
        .assign(variable=lambda df: df["variable"].replace(title_fields))
        .pipe(utils.drop_runs_tidy, value_col="value", groupby="variable")
    )

    if ylim is None:
        _y = alt.Y(
            "value:Q",
            scale=alt.Scale(domain=(0, plot_src["value"].max() * 1.10)),
            title=ylabel,
        )
    else:
        _y = alt.Y("value:Q", scale=alt.Scale(domain=ylim), title=ylabel,)

    if xlim is None:
        _x = alt.X("date:T")
    else:
        _x = alt.X("date:T", scale=alt.Scale(domain=xlim))

    base = (
        alt.Chart(plot_src)
        .mark_line(interpolate=interpolate)
        .encode(
            x=_x,
            y=_y,  # alt.Y("value:Q", title=ylabel),
            color=alt.Color(
                "variable",
                sort=list(title_fields.values()),
                legend=alt.Legend(title=None),
            ),
        )
    )

    selectors = (
        base.mark_point()
        .encode(x="date:T", y="value:Q", opacity=alt.value(0),)
        .add_selection(nearest)
    )

    points = (
        base.mark_point()
        .encode(opacity=alt.condition(nearest, alt.value(1), alt.value(0)),)
        .properties(width=600, height=100)
    )

    # Draw text labels near the points, and highlight based on selection
    text = base.mark_text(align="left", dx=5, dy=-5).encode(
        text=alt.condition(
            nearest, "value:N", alt.value(" "), format=f",.{text_sigfigs}r"
        )
    )

    rules = (
        alt.Chart(plot_src)
        .mark_rule(color="gray")
        .encode(x="date:T",)
        .transform_filter(nearest)
    )

    return base, selectors, rules, points, text


def make_plot(source: pandas.DataFrame) -> alt.TopLevelMixin:
    brush = alt.selection(type="interval", encodings=["x"])

    _precip_vars = ["rainfall_depth"]
    precip_gp = make_layer(
        source,
        _precip_vars,
        xlim=None,
        ylim=None,
        ylabel=["Depth", "(inches)"],
        interpolate="step-after",
    )

    precip_layer = alt.layer(
        *[i.encode(alt.X("date:T", scale=alt.Scale(domain=brush)),) for i in precip_gp]
    )

    _vol_vars = ["storage_volume"]
    vol_gp = make_layer(
        source, _vol_vars, xlim=None, ylim=None, ylabel=["Volume", "(cu-ft)"]
    )

    vol_layer = alt.layer(
        *[i.encode(alt.X("date:T", scale=alt.Scale(domain=brush)),) for i in vol_gp]
    )

    _loss_rate_vars = ["diversion_rate", "infiltration_rate"]
    loss_rate_gp = make_layer(
        source, _loss_rate_vars, xlim=None, ylim=None, ylabel=["Flowrate", "(cfs)"]
    )

    loss_rate_layer = alt.layer(
        *[
            i.encode(alt.X("date:T", scale=alt.Scale(domain=brush)),)
            for i in loss_rate_gp
        ]
    )

    _rate_vars = ["inflow_rate", "discharge_rate"]
    rate_gp = make_layer(
        source, _rate_vars, xlim=None, ylim=None, ylabel=["Flowrate", "(cfs)"]
    )

    rate_layer = alt.layer(
        *[i.encode(alt.X("date:T", scale=alt.Scale(domain=brush)),) for i in rate_gp]
    )

    _cumul_vars = [
        "inflow_volume",
        "diverted_volume",
        "infiltrated_volume",
        "discharged_volume",
    ]
    cumsum_source = (
        source.query("variable in @_cumul_vars")
        .groupby(["variable", "date"])
        .sum()
        .reset_index()
        .set_index("date")
        .groupby("variable")
        .resample("D")
        .sum()
        .groupby(level=0)
        .cumsum()
        .reset_index()
    )
    cumul_gp = make_layer(
        cumsum_source,
        _cumul_vars,
        xlim=None,
        ylim=None,
        ylabel=["Cumulative Volume", "(cu-ft)"],
    )

    cumul_layer = alt.layer(
        *[i.encode(alt.X("date:T", scale=alt.Scale(domain=brush)),) for i in cumul_gp]
    )

    sel_chart = (
        alt.layer(*rate_gp)
        .properties(height=60)
        .encode(opacity=alt.value(0.5))
        .add_selection(brush)
    )

    p = (
        alt.vconcat(
            precip_layer, vol_layer, loss_rate_layer, cumul_layer, rate_layer, sel_chart
        )
        .resolve_scale(color="independent",)
        .configure_legend(labelLimit=0, orient="top", direction="vertical", title=None)
    )

    return p
