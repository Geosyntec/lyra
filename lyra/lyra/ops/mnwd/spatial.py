import orjson

import topojson
import geopandas

from lyra.connections.azure_fs import get_file_as_bytestring
from lyra.core.cache import cache_decorator


@cache_decorator(ex=3600 * 24)  # expires in 24 hours
def _rsb_geojson_bytestring(**kwargs):
    data = get_file_as_bytestring("mnwd/drooltool/spatial/rsb_geo_4326_latest.json")

    if not kwargs:
        return data

    gdf = geopandas.read_file(data.decode(), **kwargs)

    return gdf.to_json()


def rsb_geojson(**kwargs):
    return orjson.loads(_rsb_geojson_bytestring(**kwargs))


@cache_decorator(ex=3600 * 24)  # expires in 24 hours
def _rsb_topojson_bytestring(
    bbox=None, toposimplify=0.0001, topoquantize=1e6, **kwargs
):

    data = get_file_as_bytestring("mnwd/drooltool/spatial/rsb_geo_4326_latest.json")
    gdf = geopandas.read_file(data.decode(), bbox=bbox)
    topo = topojson.Topology(
        gdf, toposimplify=toposimplify, topoquantize=topoquantize, **kwargs
    )
    return topo.to_json()


def rsb_topojson(**kwargs):
    return orjson.loads(_rsb_topojson_bytestring(**kwargs))
