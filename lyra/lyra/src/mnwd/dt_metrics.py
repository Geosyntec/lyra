from typing import List, Optional
from textwrap import dedent

import orjson
import pandas

from lyra.connections import database
from lyra.core.cache import cache_decorator
from lyra.core.errors import SQLQueryError


def _fetch_categories_df(engine):
    qry = dedent(
        f"""\
    select
        *
    from [DTMetricsCategories]
    """
    )

    with engine.begin() as conn:
        cat = pandas.read_sql(qry, con=conn,)

    return cat


@cache_decorator(ex=None)  # expires only when cache is flushed.
def _fetch_categories_as_json(engine=None):  # pragma: no cover
    if engine is None:
        engine = database.engine
    cat = _fetch_categories_df(engine)
    return cat.to_json(orient="index")


def _dt_metrics_query(
    catchidns: Optional[List[int]] = None,
    variables: Optional[List[str]] = None,
    years: Optional[List[int]] = None,
    months: Optional[List[int]] = None,
    engine=None,
):

    cat_json = _fetch_categories_as_json(engine)
    cat_dct = orjson.loads(cat_json)
    rev_cat = {}
    for _, value in cat_dct.items():
        rev_cat[value["variable_name"]] = value["variable"]

    if catchidns is None:
        catchidns, user_catch = "1=?", (1,)
    else:
        user_catch = catchidns
        catchidns = "or ".join(["catchidn = ? " for _ in catchidns])

    if variables is None:
        variables, user_var = "1=?", (1,)
    else:
        user_var = [rev_cat[i] for i in variables]
        variables = "or ".join(["variable = ? " for _ in variables])

    if years is None:
        years, user_year = "1=?", (1,)
    else:
        user_year = years
        years = "or ".join(["year = ? " for _ in years])

    if months is None:
        months, user_month = "1=?", (1,)
    else:
        user_month = months
        months = "or ".join(["month = ? " for _ in months])

    qry = dedent(
        f"""\
        select
            *
        from [DTMetrics]
        where
            ({catchidns}) and
            ({variables}) and
            ({years}) and
            ({months})
        order by
            catchidn ASC, variable ASC, year ASC, month ASC
        """
    )

    return qry, user_catch, user_var, user_year, user_month


def _fetch_dt_metrics_records(qry, user_catch, user_var, user_year, user_month, engine):

    cat_json = _fetch_categories_as_json(engine)
    cat = pandas.read_json(cat_json, orient="index").set_index("id")

    with engine.begin() as conn:
        df = pandas.read_sql(
            qry, params=(*user_catch, *user_var, *user_year, *user_month), con=conn,
        )

    if df.empty:
        data = dict(
            catchidn=user_catch, variable=user_var, year=user_year, month=user_month
        )
        raise SQLQueryError("Error: Bad Query Filters", data)

    records = (
        df.merge(cat, on="variable", how="left")
        .assign(variable=lambda df: df["variable_name"])
        .drop(columns=["variable_name"])
        .to_dict(orient="records")
    )

    return records


@cache_decorator(ex=3600 * 6)  # expires in 6 hours
def fetch_dt_metrics_as_json(
    qry, user_catch, user_var, user_year, user_month, engine=None
):  # pragma: no cover
    if engine is None:
        engine = database.engine
    records = _fetch_dt_metrics_records(
        qry, user_catch, user_var, user_year, user_month, engine
    )
    return orjson.dumps(records)


def agg_dt_metrics_df(
    records: pandas.DataFrame, agg: str, groupby: Optional[List[str]] = None,
):

    if groupby is None:
        groupby = ["variable", "year", "month"]
    else:
        groupby = [s for s in groupby if s != "value"]

    agg_records = records.groupby(groupby, as_index=False)["value"].agg(agg)

    return agg_records


@cache_decorator(ex=3600 * 6)  # expires in 6 hours
def dt_metrics(
    catchidns: Optional[List[int]] = None,
    variables: Optional[List[str]] = None,
    years: Optional[List[int]] = None,
    months: Optional[List[int]] = None,
    groupby: Optional[List[str]] = None,
    agg: Optional[str] = None,
    engine=None,
) -> bytes:  # pragma: no cover

    args = _dt_metrics_query(
        catchidns=catchidns,
        variables=variables,
        years=years,
        months=months,
        engine=engine,
    )

    data = fetch_dt_metrics_as_json(*args, engine=engine)

    if agg is None:  # early exit
        return data  # bytes
    else:
        records = pandas.DataFrame(orjson.loads(data))
        agg_records = agg_dt_metrics_df(records, agg, groupby)
        return orjson.dumps(agg_records.to_dict(orient="records"))
