from typing import Optional

import geopandas
import networkx
import orjson

from lyra.connections import azure_fs
from lyra.core.cache import cache_decorator
from lyra.src.network.algorithms import trace_downstream, trace_upstream
from lyra.src.network.utils import graph_from_df


def construct_rsb_graph_from_mnwd_geojson(
    geojson_file: Optional[str] = None,
    share: Optional[str] = None,
    source: Optional[str] = None,
    target: Optional[str] = None,
) -> networkx.DiGraph:
    if geojson_file is None:
        file = "mnwd/drooltool/spatial/rsb_geo_4326_latest.json"
        geojson_file = azure_fs.get_file_as_bytestring(file, share=share).decode()

    if source is None:
        source = "CatchIDN"
    if target is None:
        target = "DwnCatchIDN"

    gdf = (
        geopandas.read_file(geojson_file)
        .assign(rep_pt=lambda df: df.geometry.representative_point())
        .assign(rep_x=lambda df: df["rep_pt"].x)
        .assign(rep_y=lambda df: df["rep_pt"].y)
        .drop(columns=["geometry", "rep_pt"])
    )

    g = graph_from_df(gdf, source, target)
    if 0 in gdf[target]:
        networkx.set_node_attributes(
            g, {0: {"rep_x": 0, "rep_y": 0, "Watershed": "Ocean"}}
        )

    return g


@cache_decorator(ex=None)  #
def construct_rsb_graph_from_mnwd_geojson_bytestring(
    geojson_file: Optional[str] = None,
    share: Optional[str] = None,
    source: Optional[str] = None,
    target: Optional[str] = None,
) -> bytes:

    g = construct_rsb_graph_from_mnwd_geojson(
        geojson_file=geojson_file, share=share, source=source, target=target
    )

    return orjson.dumps(g, default=networkx.node_link_data)


@cache_decorator(ex=3600 * 6)  # expires in 6 hours
def rsb_upstream_trace(
    catchidn: int,
    geojson_file: Optional[str] = None,
    share: Optional[str] = None,
    source: Optional[str] = None,
    target: Optional[str] = None,
):
    gbytes = construct_rsb_graph_from_mnwd_geojson_bytestring(
        geojson_file=geojson_file, share=share, source=source, target=target
    )
    g = networkx.node_link_graph(orjson.loads(gbytes))
    upstream = sorted(trace_upstream(g, catchidn))

    return orjson.dumps(upstream)


@cache_decorator(ex=3600 * 6)  # expires in 6 hours
def rsb_downstream_trace(
    catchidn: int,
    geojson_file: Optional[str] = None,
    share: Optional[str] = None,
    source: Optional[str] = None,
    target: Optional[str] = None,
):
    gbytes = construct_rsb_graph_from_mnwd_geojson_bytestring(
        geojson_file=geojson_file, share=share, source=source, target=target
    )
    g = networkx.node_link_graph(orjson.loads(gbytes))
    downstream = sorted(trace_downstream(g, catchidn))

    return orjson.dumps(downstream)
