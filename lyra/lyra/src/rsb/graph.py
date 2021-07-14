import io
from typing import Optional

import networkx
import orjson
import pandas

from lyra.core import utils
from lyra.core.cache import cache_decorator
from lyra.src.network.algorithms import trace_downstream, trace_upstream
from lyra.src.network.utils import graph_from_df


def construct_rsb_graph_from_mnwd_geojson(
    file_contents: Optional[str] = None,
    share: Optional[str] = None,
    source: Optional[str] = None,
    target: Optional[str] = None,
) -> networkx.DiGraph:

    if file_contents is None:
        file_contents = utils.local_path(
            "data/mount/swn/mnwd/drooltool/spatial/rsb_geo_data_latest.csv"
        ).read_text()

    if source is None:
        source = "CatchIDN"
    if target is None:
        target = "DwnCatchIDN"

    df = pandas.read_csv(io.StringIO(file_contents))

    g = graph_from_df(df, source, target)
    if 0 in df[target]:
        networkx.set_node_attributes(
            g, {0: {"rep_x": 0, "rep_y": 0, "Watershed": "Ocean"}}
        )

    return g


@cache_decorator(ex=None)  #
def construct_rsb_graph_from_mnwd_geojson_bytestring(
    file_contents: Optional[str] = None,
    share: Optional[str] = None,
    source: Optional[str] = None,
    target: Optional[str] = None,
) -> bytes:

    g = construct_rsb_graph_from_mnwd_geojson(
        file_contents=file_contents, share=share, source=source, target=target
    )

    return orjson.dumps(g, default=networkx.node_link_data)


@cache_decorator(ex=3600 * 6)  # expires in 6 hours
def rsb_upstream_trace(
    catchidn: int,
    file_contents: Optional[str] = None,
    share: Optional[str] = None,
    source: Optional[str] = None,
    target: Optional[str] = None,
) -> bytes:
    gbytes = construct_rsb_graph_from_mnwd_geojson_bytestring(
        file_contents=file_contents, share=share, source=source, target=target
    )
    g = networkx.node_link_graph(orjson.loads(gbytes))
    upstream = sorted(trace_upstream(g, catchidn))

    return orjson.dumps(upstream)


@cache_decorator(ex=3600 * 6)  # expires in 6 hours
def rsb_downstream_trace(
    catchidn: int,
    file_contents: Optional[str] = None,
    share: Optional[str] = None,
    source: Optional[str] = None,
    target: Optional[str] = None,
) -> bytes:
    gbytes = construct_rsb_graph_from_mnwd_geojson_bytestring(
        file_contents=file_contents, share=share, source=source, target=target
    )
    g = networkx.node_link_graph(orjson.loads(gbytes))
    downstream = sorted(trace_downstream(g, catchidn))

    return orjson.dumps(downstream)
