import importlib

import pytest
import pandas

from lyra.connections import database, schemas, azure_fs
from lyra.src.mnwd import helper


def test_engine(empty_engine):
    engine = empty_engine
    file = importlib.resources.open_text("lyra.tests.data", "test_dt_metrics.csv")
    helper.set_drooltool_database_with_file(engine, file=file)

    df = pandas.read_sql("select * from DTMetrics limit 5", con=engine)
    assert len(df) == 5

    df = pandas.read_sql("select * from TableChangeLog limit 5", con=engine)
    assert len(df) == 2


def test_engine_file_is_none(monkeypatch, empty_engine):
    engine = empty_engine

    def mock_get_file_object(*args, **kwargs):
        file = importlib.resources.open_text("lyra.tests.data", "test_dt_metrics.csv")
        return file

    monkeypatch.setattr(azure_fs, "get_file_object", mock_get_file_object)

    helper.set_drooltool_database_with_file(engine, file=None)

    df = pandas.read_sql("select * from DTMetrics limit 5", con=engine)
    assert len(df) == 5

    df = pandas.read_sql("select * from TableChangeLog limit 5", con=engine)
    assert len(df) == 2


def test_engine_has_data(monkeypatch, data_engine):
    engine = data_engine

    def mock_get_file_object(*args, **kwargs):
        file = importlib.resources.open_text("lyra.tests.data", "test_dt_metrics.csv")
        return file

    monkeypatch.setattr(azure_fs, "get_file_object", mock_get_file_object)

    helper.set_drooltool_database_with_file(engine, file=None)

    df = pandas.read_sql("select * from DTMetrics limit 5", con=engine)
    assert len(df) == 5

    df = pandas.read_sql("select * from TableChangeLog limit 5", con=engine)
    assert len(df) == 4
