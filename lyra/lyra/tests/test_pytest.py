import pytest

# from osgeo import gdal, ogr, osr
from fiona.ogrext import ItemsIterator, Iterator, KeysIterator
from geopandas import GeoDataFrame

# from lyra.core.config import settings
# from lyra.connections.database import get_connection_string
from lyra.tests import utils

# print("before: ", settings.AZURE_DATABASE_SERVER)
# settings.AZURE_DATABASE_SERVER = None
# print("after: ", settings.AZURE_DATABASE_SERVER)


def test_pytest():
    assert True


@pytest.mark.parametrize("file", [utils._rsb_geo_file(), utils._rsb_geo_file_path()])
def test_geopandas(file):
    import geopandas

    gdf = geopandas.read_file(file)
    gdf.to_crs("EPSG:4326")
