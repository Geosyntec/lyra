from typing import Any, Dict, List

import altair as alt
import pandas

from lyra.src.diversion import simulate_diversion


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
    df = (
        simulate_diversion(**kwargs)  # type: ignore
        .reset_index()
        .melt(id_vars="date")
        .round(4)
    )
    return df


def make_summary_table(df):
    table: dict = {
        "column_names": None,
        "records": [],
    }
    inflow_vol = df.query('variable == "inflow_volume"')["value"].sum()
    diverted_vol = df.query('variable == "diverted_volume"')["value"].sum()
    diverted_pct = diverted_vol / inflow_vol

    infiltrated_vol = df.query('variable == "infiltrated_volume"')["value"].sum()
    infiltrated_pct = infiltrated_vol / inflow_vol

    bypassed_vol = df.query('variable == "bypassed_volume"')["value"].sum()
    bypassed_pct = bypassed_vol / inflow_vol

    records = [
        {
            "label": "Total Inflow Volume",
            "units": "cuft",
            "value": f"{ inflow_vol : 0,.0f}".strip(),
            "description": f"Total volume entering the diversion during the scenario.",
        },
        {
            "label": "Total Diverted Volume",
            "units": "cuft",
            "value": f"{ diverted_vol : 0,.0f}".strip(),
            "description": f"Total volume diverted during this scenario.",
        },
        {
            "label": r"% of Inflow Diverted",
            "units": "%",
            "value": f"{ diverted_pct : 0.1%}".strip(),
            "description": f"Diverted volume as percentage of inflow volume.",
        },
        {
            "label": "Total Infiltrated Volume",
            "units": "cuft",
            "value": f"{ infiltrated_vol : 0,.0f}".strip(),
            "description": f"Total volume infiltrated during this scenario.",
        },
        {
            "label": r"% of Inflow Infiltrated",
            "units": "%",
            "value": f"{ infiltrated_pct : 0.1%}".strip(),
            "description": f"Infiltrated volume as percentage of inflow volume.",
        },
        {
            "label": "Total Bypassd Volume",
            "units": "cuft",
            "value": f"{ bypassed_vol : 0,.0f}".strip(),
            "description": f"Total volume bypassed during this scenario.",
        },
        {
            "label": r"% of Inflow Bypassd",
            "units": "%",
            "value": f"{ bypassed_pct : 0.1%}".strip(),
            "description": f"Bypassed volume as percentage of inflow volume.",
        },
    ]

    table["records"] = records

    return table


def make_layer(
    source,
    fields,
    xlim=None,
    ylim=None,
    text_sigfigs=3,
    ylabel=None,
    interpolate=None,
    reverse_y=False,
    width=600,
    height=100,
):

    if interpolate is None:
        interpolate = alt.Undefined

    nearest = alt.selection_single(
        nearest=True, on="mouseover", fields=["date"], empty="none", clear="mouseout",
    )

    title_fields = {s: s.title().replace("_", " ") for s in fields}

    plot_src = (
        source.query("variable in @fields").assign(
            variable=lambda df: df["variable"].replace(title_fields)
        )
        ## Don't tidy up, we need values at every 'rule' so that the tool tip is correct.
        ## inefficient, but accurate.
        # .pipe(utils.drop_runs_tidy, value_col="value", groupby=["variable"])
    )

    if ylim is None:
        _y = alt.Y(
            "value:Q",
            scale=alt.Scale(
                domain=(0, plot_src["value"].max() * 1.10), reverse=reverse_y
            ),
            title=ylabel,
        )
    else:
        _y = alt.Y(
            "value:Q", scale=alt.Scale(domain=ylim, reverse=reverse_y), title=ylabel
        )

    if xlim is None:
        _x = alt.X("date:T")
    else:
        _x = alt.X("date:T", scale=alt.Scale(domain=xlim))

    base = alt.Chart(plot_src).properties(width=width, height=height).encode(x=_x)

    lines = base.mark_line(interpolate=interpolate).encode(
        y=_y,
        color=alt.Color(
            "variable", sort=list(title_fields.values()), legend=alt.Legend(title=None),
        ),
    )

    points = lines.mark_point().transform_filter(nearest).encode(opacity=alt.value(1))

    # Draw text labels near the points, and highlight based on selection

    tt_labels = sorted(plot_src.variable.unique())

    rule = (
        base.transform_pivot("variable", value="value", groupby=["date"])
        .mark_rule()
        .encode(
            opacity=alt.condition(nearest, alt.value(0.3), alt.value(0)),
            tooltip=[alt.Tooltip("date", format="%b %-d, %Y@%H:%M", title="Date"),]
            + [
                alt.Tooltip(c, type="quantitative", format=f",.{text_sigfigs}r")
                for c in tt_labels
            ],
        )
        .add_selection(nearest)
    )

    return lines, points, rule


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
        *[
            i.encode(
                alt.X(
                    "date:T",
                    scale=alt.Scale(domain=brush),
                    title=" ",
                    axis=alt.Axis(labels=False),
                )
            )
            for i in precip_gp
        ]
    )

    _vol_vars = ["storage_volume"]
    vol_gp = make_layer(
        source, _vol_vars, xlim=None, ylim=None, ylabel=["Volume", "(cu-ft)"]
    )

    vol_layer = alt.layer(
        *[
            i.encode(
                alt.X(
                    "date:T",
                    scale=alt.Scale(domain=brush),
                    title=" ",
                    axis=alt.Axis(labels=False),
                )
            )
            for i in vol_gp
        ]
    )

    _loss_rate_vars = ["diversion_rate", "infiltration_rate"]
    loss_rate_gp = make_layer(
        source, _loss_rate_vars, xlim=None, ylim=None, ylabel=["Flowrate", "(cfs)"]
    )

    loss_rate_layer = alt.layer(
        *[
            i.encode(
                alt.X(
                    "date:T",
                    scale=alt.Scale(domain=brush),
                    title=" ",
                    axis=alt.Axis(labels=False),
                )
            )
            for i in loss_rate_gp
        ]
    )

    _rate_vars = ["inflow_rate", "bypass_rate"]
    rate_gp = make_layer(
        source, _rate_vars, xlim=None, ylim=None, ylabel=["Flowrate", "(cfs)"]
    )

    rate_layer = alt.layer(
        *[
            i.encode(alt.X("date:T", scale=alt.Scale(domain=brush), title=" "))
            for i in rate_gp
        ]
    )

    _cumul_vars = [
        "inflow_volume",
        "diverted_volume",
        "infiltrated_volume",
        "bypassed_volume",
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
        *[
            i.encode(
                alt.X(
                    "date:T",
                    scale=alt.Scale(domain=brush),
                    title=" ",
                    axis=alt.Axis(labels=False),
                )
            )
            for i in cumul_gp
        ]
    )

    sel_chart_height = 60
    discharge = alt.layer(
        make_layer(
            source,
            _rate_vars,
            xlim=None,
            ylim=None,
            ylabel=["Flowrate (cfs)"],
            height=sel_chart_height,
        )[0]
    )
    precip = alt.layer(
        make_layer(
            source,
            _precip_vars,
            xlim=None,
            ylim=None,
            ylabel=["Depth (inches)"],
            interpolate="step-after",
            reverse_y=True,
            height=sel_chart_height,
        )[0]
    )

    sel_chart = (
        alt.layer(precip, discharge)
        .properties(
            title=alt.TitleParams(
                "Click and drag to select date-range",
                color=alt.Value("dimgray"),
                dy=sel_chart_height / 1.5,
            ),
        )
        .encode(opacity=alt.value(0.5))
        .resolve_scale(y="independent")
        .add_selection(brush)
    )

    p = (
        alt.vconcat(
            precip_layer, vol_layer, loss_rate_layer, cumul_layer, rate_layer, sel_chart
        )
        .resolve_scale(color="independent",)
        .configure_concat(spacing=2)
        # .configure_legend(labelLimit=0, orient="top", direction="vertical", title=None)
    )

    return p
