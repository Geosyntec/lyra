from typing import Optional, List, Tuple
from io import StringIO

import geopandas
import orjson
import pandas
import topojson

from lyra.connections import azure_fs
from lyra.core.cache import cache_decorator


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

    data = azure_fs.get_file_as_bytestring(
        "mnwd/drooltool/spatial/rsb_geo_data_latest.csv"
    )

    df = pandas.read_csv(StringIO(data.decode())).pipe(
        _filter_rsb_df, watersheds, catchidns
    )

    return orjson.dumps(df.to_dict(orient="records"))


def rsb_data(**kwargs):
    return orjson.loads(_rsb_data_bytestring(**kwargs))


@cache_decorator(ex=3600 * 24)  # expires in 24 hours
def _rsb_geojson_bytestring(
    bbox: Optional[Tuple[float, float, float, float]] = None,
    watersheds: Optional[List[str]] = None,
    catchidns: Optional[List[str]] = None,
    **kwargs,
) -> bytes:
    data = azure_fs.get_file_as_bytestring(
        "mnwd/drooltool/spatial/rsb_geo_4326_latest.json"
    )

    if not any([bbox, watersheds, catchidns]):
        return data

    gdf = geopandas.read_file(data.decode(), bbox=bbox).pipe(
        _filter_rsb_df, watersheds, catchidns
    )

    return gdf.to_json().encode()


def rsb_geojson(**kwargs) -> dict:
    return orjson.loads(_rsb_geojson_bytestring(**kwargs))


@cache_decorator(ex=3600 * 24)  # expires in 24 hours
def _rsb_topojson_bytestring(
    bbox=None,
    watersheds: Optional[List[str]] = None,
    catchidns: Optional[List[str]] = None,
    toposimplify: Optional[float] = None,
    topoquantize: Optional[float] = None,
    **kwargs,
) -> bytes:

    data = _rsb_geojson_bytestring(
        bbox=bbox, watersheds=watersheds, catchidns=catchidns
    )
    gdf = geopandas.read_file(data.decode())

    if toposimplify is None:  # pragma: no cover
        toposimplify = 0.0001
    if topoquantize is None:  # pragma: no cover
        topoquantize = 1e6

    topo = topojson.Topology(
        gdf, toposimplify=toposimplify, topoquantize=topoquantize, **kwargs
    )
    return topo.to_json().encode()


def rsb_topojson(**kwargs):
    return orjson.loads(_rsb_topojson_bytestring(**kwargs))


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
    **kwargs,
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

    data = None
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
            **kwargs,
        )
    else:
        raise ValueError(f"Unknown output format: `{f}`")

    return data
