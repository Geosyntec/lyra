from io import StringIO
from typing import Any, List, Optional, Tuple

import geopandas
import orjson
import pandas
import topojson

from lyra.core.cache import cache_decorator
from lyra.core import utils


def _filter_rsb_df(
    df: pandas.DataFrame,
    watersheds: Optional[List[str]] = None,
    catchidns: Optional[List[str]] = None,
) -> pandas.DataFrame:

    _q = []

    if watersheds is not None:
        _q.append(f"Watershed in @watersheds")
    if catchidns is not None:
        _q.append(f"CatchIDN in @catchidns")

    if _q:
        query = " & ".join(_q)
        return df.query(query)

    return df


@cache_decorator(ex=3600 * 24)  # expires in 24 hours
def _rsb_data_bytestring(
    watersheds: Optional[List[str]] = None, catchidns: Optional[List[str]] = None,
) -> bytes:

    data = utils.local_path(
        "data/mount/swn/mnwd/drooltool/spatial/rsb_geo_data_latest.csv"
    )

    df = pandas.read_csv(data).pipe(_filter_rsb_df, watersheds, catchidns)

    return orjson.dumps(df.to_dict(orient="records"))


def rsb_data(**kwargs):
    return orjson.loads(_rsb_data_bytestring(**kwargs))


@cache_decorator(ex=3600 * 24)  # expires in 24 hours
def _rsb_geojson_bytestring(
    bbox: Optional[Tuple[float, float, float, float]] = None,
    watersheds: Optional[List[str]] = None,
    catchidns: Optional[List[str]] = None,
) -> bytes:

    data = utils.local_path(
        "data/mount/swn/mnwd/drooltool/spatial/rsb_geo_4326_latest.json"
    )

    if not any([bbox, watersheds, catchidns]):
        return data.read_bytes()

    gdf = geopandas.read_file(data, bbox=bbox).pipe(
        _filter_rsb_df, watersheds, catchidns
    )

    result: bytes = gdf.to_json().encode()

    return result


def rsb_geojson(**kwargs: Any) -> dict:
    rsp: dict = orjson.loads(_rsb_geojson_bytestring(**kwargs))
    return rsp


@cache_decorator(ex=3600 * 24)  # expires in 24 hours
def _rsb_topojson_bytestring(
    bbox: Optional[Tuple[float, float, float, float]] = None,
    watersheds: Optional[List[str]] = None,
    catchidns: Optional[List[str]] = None,
    toposimplify: Optional[float] = None,
    topoquantize: Optional[float] = None,
) -> bytes:

    data = _rsb_geojson_bytestring(
        bbox=bbox, watersheds=watersheds, catchidns=catchidns
    )
    gdf = geopandas.read_file(data.decode())

    if toposimplify is None:  # pragma: no cover
        toposimplify = 0.0001
    if topoquantize is None:  # pragma: no cover
        topoquantize = 1e6

    topo = topojson.Topology(gdf, toposimplify=toposimplify, topoquantize=topoquantize)
    result: bytes = topo.to_json().encode()
    return result


def rsb_topojson(**kwargs):
    rsp: dict = orjson.loads(_rsb_topojson_bytestring(**kwargs))
    return rsp


@cache_decorator(ex=3600 * 6)  # expires in 6 hours
def rsb_spatial(
    f: Optional[str] = None,
    xmin: Optional[float] = None,
    ymin: Optional[float] = None,
    xmax: Optional[float] = None,
    ymax: Optional[float] = None,
    watersheds: Optional[List[str]] = None,
    catchidns: Optional[List[str]] = None,
    toposimplify: Optional[float] = None,
    topoquantize: Optional[float] = None,
    **kwargs: Any,
) -> bytes:

    f = f or "topojson"

    # aliso ck is ~ bbox = {"xmin":-117.78,"ymin":33.45,"xmax":-117.58,"ymax":33.72}
    xmin = xmin or -117.78
    ymin = ymin or 33.45
    xmax = xmax or -117.58
    ymax = ymax or 33.72
    bbox = (xmin, ymin, xmax, ymax)

    if toposimplify is None:  # pragma: no branch
        toposimplify = 0.0001
    if topoquantize is None:  # pragma: no branch
        topoquantize = 1e6

    data: bytes = orjson.dumps(None)
    if f == "geojson":
        data = _rsb_geojson_bytestring(
            bbox=bbox, watersheds=watersheds, catchidns=catchidns,
        )

    elif f == "topojson":
        data = _rsb_topojson_bytestring(
            bbox=bbox,
            watersheds=watersheds,
            catchidns=catchidns,
            toposimplify=toposimplify,
            topoquantize=topoquantize,
        )
    else:
        raise ValueError(f"Unknown output format: `{f}`")

    return data
