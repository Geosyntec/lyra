import importlib

import pytest

from lyra.connections import azure_fs, database, schemas
from lyra.core import cache
from lyra.src.mnwd import helper
from lyra.tests import utils


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as requireing a data connection"
    )


@pytest.fixture
def reconnect_engine():
    database.reconnect_engine(database.engine)
    yield


@pytest.fixture
def empty_engine():
    engine = database.create_engine("sqlite:///")
    schemas.init_all(engine)

    yield engine


@pytest.fixture
def data_engine():
    engine = database.create_engine("sqlite:///")
    schemas.init_all(engine)

    with importlib.resources.path("lyra.tests.data", "test_dt_metrics.csv") as p:
        filepath = p
    helper.set_drooltool_database_with_file(engine, file=filepath)

    yield engine


@pytest.fixture
def nocache():
    cache.use_cache(False)
    yield
    cache.use_cache(True)


@pytest.fixture
def clearcache():
    cache.flush()
    yield


@pytest.fixture
def mock_rsb_geo_bytestring(monkeypatch):
    monkeypatch.setattr(azure_fs, "get_file_as_bytestring", utils._rsb_geo_file_binary)


@pytest.fixture
def mock_rsb_data_bytestring(monkeypatch):
    monkeypatch.setattr(azure_fs, "get_file_as_bytestring", utils._rsb_data_file_binary)


@pytest.fixture
def mock_get_MNWD_file_obj_metrics(monkeypatch):
    monkeypatch.setattr(helper, "get_MNWD_file_obj", utils._rsb_metrics_file)


@pytest.fixture
def mock_get_MNWD_file_obj_geo(monkeypatch):
    monkeypatch.setattr(helper, "get_MNWD_file_obj", utils._rsb_geo_file)


@pytest.fixture()
def mock_azure_get_dt_metrics_file_object(monkeypatch):
    monkeypatch.setattr(azure_fs, "get_file_object", utils._dt_metrics_file)


@pytest.fixture(autouse=True)
def mock_azure_put_file_object(monkeypatch):
    monkeypatch.setattr(azure_fs, "put_file_object", utils._azure_put_file_object)
