from functools import lru_cache
from typing import Dict, Tuple, Union

import networkx as nx
import orjson as json


@lru_cache(maxsize=100)
def _cached_layout(
    edge_json: str, prog: str
) -> Dict[Union[str, int], Tuple[float, float]]:  # pragma: no cover
    g = nx.from_edgelist(json.loads(edge_json), create_using=nx.MultiDiGraph)
    layout: Dict[Union[str, int], Tuple[float, float]] = nx.nx_pydot.pydot_layout(
        g, prog=prog
    )
    return layout


def cached_layout(
    g: nx.Graph, prog: str = "dot"
) -> Dict[Union[str, int], Tuple[float, float]]:  # pragma: no cover
    edges = sorted(g.edges(), key=lambda x: str(x))
    edge_json = json.dumps(list(edges))
    return _cached_layout(edge_json, prog=prog)
