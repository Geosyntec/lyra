import orjson
import pytest

from lyra.src.mnwd import spatial


def test_rsb_geojson(
    nocache, mock_rsb_geo_bytestring,
):
    rsb = spatial.rsb_geojson()
    features = rsb["features"]
    assert len(features) == 10


def test_rsb_topojson(
    nocache, mock_rsb_geo_bytestring,
):
    rsb = spatial.rsb_topojson()
    features = rsb["objects"]["data"]["geometries"]
    assert len(features) == 10


@pytest.mark.parametrize("catchidns", [None, [10], [214, 328]])
@pytest.mark.parametrize("watersheds", [None, "Aliso"])
@pytest.mark.parametrize("format", ["topojson", "geojson", "error"])
def test_rsb_spatial(
    nocache, mock_rsb_geo_bytestring, format, catchidns, watersheds,
):
    if format == "error":
        with pytest.raises(ValueError):
            rsb = spatial.rsb_spatial(
                f=format, catchidns=catchidns, watersheds=watersheds
            )
    else:
        rsb = spatial.rsb_spatial(f=format, catchidns=catchidns, watersheds=watersheds)
        data = orjson.loads(rsb)
        n = -1
        if format == "topojson":
            assert "objects" in data
            n = len(data["objects"]["data"]["geometries"])

        if format == "geojson":
            assert "features" in data
            n = len(data["features"])

        if catchidns is not None:
            assert n == len(catchidns)
        else:
            assert (
                n == 10
            ), "there are 10 catchidn's in the test graph, all are in Aliso"
