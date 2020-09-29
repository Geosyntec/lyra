import importlib

import pytest

from lyra.connections import database, schemas, azure_fs
from lyra.src.mnwd import helper
from lyra.core import cache
from lyra.tests import utils


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as requireing a data connection"
    )


@pytest.fixture
def empty_engine():
    engine = database.create_engine("sqlite:///")
    schemas.init_all(engine)

    yield engine


@pytest.fixture
def data_engine():
    engine = database.create_engine("sqlite:///")
    schemas.init_all(engine)
    file = importlib.resources.open_text("lyra.tests.data", "test_dt_metrics.csv")
    helper.set_drooltool_database_with_file(engine, file=file)

    yield engine


@pytest.fixture
def nocache():
    cache.use_cache(False)
    yield
    cache.use_cache(True)


@pytest.fixture
def mock_rsb_geo_bytestring(monkeypatch):
    monkeypatch.setattr(azure_fs, "get_file_as_bytestring", utils._rsb_geo_file_binary)


@pytest.fixture
def mock_get_MNWD_file_obj_metrics(monkeypatch):
    monkeypatch.setattr(helper, "get_MNWD_file_obj", utils._rsb_metrics_file)


@pytest.fixture
def mock_get_MNWD_file_obj_geo(monkeypatch):
    monkeypatch.setattr(helper, "get_MNWD_file_obj", utils._rsb_geo_file)


@pytest.fixture(autouse=True)
def mock_azure_put_file_object(monkeypatch):
    monkeypatch.setattr(azure_fs, "put_file_object", utils._azure_put_file_object)
