from textwrap import dedent
from typing import Any, Dict, List, Optional, Tuple, Union

import orjson
import pandas
from sqlalchemy.engine import Engine

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

    database.reconnect_engine(engine)
    with engine.begin() as conn:
        cat = pandas.read_sql(qry, con=conn,)

    return cat


@cache_decorator(ex=None)  # expires only when cache is flushed.
def _fetch_categories_as_json(
    engine: Optional[Engine] = None,
) -> bytes:  # pragma: no cover
    if engine is None:
        engine = database.engine
    cat = _fetch_categories_df(engine)
    result: bytes = cat.to_json(orient="index").encode()
    return result


def _dt_metrics_query(
    catchidns: Optional[List[int]] = None,
    variables: Optional[List[str]] = None,
    years: Optional[List[int]] = None,
    months: Optional[List[int]] = None,
    engine: Engine = None,
) -> Tuple[str, List[int], List[int], List[int], List[int]]:

    cat_json = _fetch_categories_as_json(engine)
    cat_dct = orjson.loads(cat_json)
    rev_cat = {}
    for _, value in cat_dct.items():
        rev_cat[value["variable_name"]] = value["variable"]

    if catchidns is None:
        catchidns_str, user_catch = "1=?", [1,]
    else:
        user_catch = catchidns
        catchidns_str = "or ".join(["catchidn = ? " for _ in catchidns])

    if variables is None:
        variables_str, user_var = "1=?", [1,]
    else:
        user_var = [rev_cat[i] for i in variables]
        variables_str = "or ".join(["variable = ? " for _ in variables])

    if years is None:
        years_str, user_year = "1=?", [1,]
    else:
        user_year = years
        years_str = "or ".join(["year = ? " for _ in years])

    if months is None:
        months_str, user_month = "1=?", [1,]
    else:
        user_month = months
        months_str = "or ".join(["month = ? " for _ in months])

    qry = dedent(
        f"""\
        select
            *
        from [DTMetrics]
        where
            ({catchidns_str}) and
            ({variables_str}) and
            ({years_str}) and
            ({months_str})
        order by
            catchidn ASC, variable ASC, year ASC, month ASC
        """
    )

    return qry, user_catch, user_var, user_year, user_month


def _fetch_dt_metrics_records(
    qry: str,
    user_catch: List[int],
    user_var: List[int],
    user_year: List[int],
    user_month: List[int],
    engine: Engine,
) -> List[Dict[str, Any]]:

    cat_json = _fetch_categories_as_json(engine)
    cat = pandas.read_json(cat_json, orient="index").set_index("id")

    database.reconnect_engine(engine)
    with engine.begin() as conn:
        df = pandas.read_sql(
            qry, params=(*user_catch, *user_var, *user_year, *user_month), con=conn,
        )

    if df.empty:
        data = dict(
            catchidn=user_catch, variable=user_var, year=user_year, month=user_month
        )
        raise SQLQueryError("Error: Bad Query Filters", data)

    records: List[Dict[str, Any]] = (
        df.merge(cat, on="variable", how="left")
        .assign(variable=lambda df: df["variable_name"])
        .drop(columns=["variable_name"])
        .to_dict(orient="records")
    )

    return records


@cache_decorator(ex=3600 * 6)  # expires in 6 hours
def fetch_dt_metrics_as_json(
    qry: str,
    user_catch: List[int],
    user_var: List[int],
    user_year: List[int],
    user_month: List[int],
    engine: Optional[Engine] = None,
) -> bytes:  # pragma: no cover
    if engine is None:
        engine = database.engine
    records = _fetch_dt_metrics_records(
        qry, user_catch, user_var, user_year, user_month, engine
    )
    result: bytes = orjson.dumps(records)
    return result


def agg_dt_metrics_df(
    records: pandas.DataFrame, agg: str, groupby: Optional[List[str]] = None,
) -> pandas.DataFrame:

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
    engine: Optional[Engine] = None,
) -> bytes:  # pragma: no cover

    args = _dt_metrics_query(
        catchidns=catchidns,
        variables=variables,
        years=years,
        months=months,
        engine=engine,
    )

    data: bytes = fetch_dt_metrics_as_json(*args, engine=engine)

    if agg is None:  # early exit
        return data  # bytes
    else:
        records = pandas.DataFrame(orjson.loads(data))
        agg_records = agg_dt_metrics_df(records, agg, groupby)
        result: bytes = orjson.dumps(agg_records.to_dict(orient="records"))
        return result
