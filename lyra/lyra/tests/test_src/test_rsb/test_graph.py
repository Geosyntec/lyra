import orjson
import pytest

from lyra.src.rsb import graph


def test_graph(nocache, mock_rsb_data_path):
    g = graph.construct_rsb_graph_from_mnwd_geojson()
    assert len(g.nodes) == 11  # the test file has 11. The 'live' file has 2k+
    assert g.is_directed, "must be a directed graph"


@pytest.mark.parametrize(
    "node, exp",
    [(10, [10, 23, 328, 214, 213, 278, 211, 212, 216, 210]), (328, [328, 214, 213]),],
)
def test_upstream_from(nocache, mock_rsb_data_path, node, exp):
    us = orjson.loads(graph.rsb_upstream_trace(node))
    assert sorted(exp) == us


@pytest.mark.parametrize(
    "node, exp",
    [
        (10, [10, 24]),  # 24 is not in the plot, but it is in the gdf.
        (216, [216, 23, 10, 24]),
        (210, [210, 216, 23, 10, 24]),
    ],
)
def test_downstream_from(nocache, mock_rsb_data_path, node, exp):
    us = orjson.loads(graph.rsb_downstream_trace(node))
    assert sorted(exp) == us


@pytest.mark.integration
def test_graph_integration():
    g = graph.construct_rsb_graph_from_mnwd_geojson()
    assert len(g.nodes) > 2000  # the test file has 11. The 'live' file has 2k+
    assert g.is_directed, "must be a directed graph"
