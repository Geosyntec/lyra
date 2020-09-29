import pytest

# from osgeo import gdal, ogr, osr
from fiona.ogrext import Iterator, ItemsIterator, KeysIterator
from geopandas import GeoDataFrame

from lyra.core.config import settings
from lyra.connections.database import get_connection_string

# print("before: ", settings.AZURE_DATABASE_SERVER)
# settings.AZURE_DATABASE_SERVER = None
# print("after: ", settings.AZURE_DATABASE_SERVER)


def test_pytest():
    assert True


# def test_constr():
#     print(get_connection_string())
