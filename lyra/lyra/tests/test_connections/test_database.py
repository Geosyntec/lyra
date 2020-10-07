import pandas

from lyra.src.mnwd import helper
from lyra.tests import utils


def test_engine(empty_engine):
    engine = empty_engine

    helper.set_drooltool_database_with_file(engine, file=utils._dt_metrics_file_path())

    df = pandas.read_sql("select * from DTMetrics limit 5", con=engine)
    assert len(df) == 5

    df = pandas.read_sql("select * from TableChangeLog limit 5", con=engine)
    assert len(df) == 2


def test_engine_file_is_none(mock_azure_get_dt_metrics_file_object, empty_engine):
    engine = empty_engine

    helper.set_drooltool_database_with_file(engine, file=None)

    df = pandas.read_sql("select * from DTMetrics limit 5", con=engine)
    assert len(df) == 5

    df = pandas.read_sql("select * from TableChangeLog limit 5", con=engine)
    assert len(df) == 2


def test_engine_has_data(mock_azure_get_dt_metrics_file_object, data_engine):
    engine = data_engine

    helper.set_drooltool_database_with_file(engine, file=None)

    df = pandas.read_sql("select * from DTMetrics limit 5", con=engine)
    assert len(df) == 5

    df = pandas.read_sql("select * from TableChangeLog limit 5", con=engine)
    assert len(df) == 4
