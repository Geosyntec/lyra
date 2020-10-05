import numpy
import pandas
import pydantic
import pytest

from lyra.src.timeseries import Timeseries
from lyra.src.viz import single_variable


def mock_timeseries(periods, freq):
    return pandas.Series(
        data=numpy.random.random(periods) * 10,
        index=pandas.date_range(start="2010-01-01", periods=periods, freq=freq,),
    )


@pytest.fixture
def offline_timeseries(monkeypatch):
    count = 5
    monkeypatch.setattr(
        Timeseries, "_init_hydstra", lambda x: mock_timeseries(count, "D")
    )
    monkeypatch.setattr(
        Timeseries, "_init_dt_metrics", lambda x: mock_timeseries(count, "MS")
    )


@pytest.mark.parametrize("sites", [["test"], ["test1", "test2"]])
@pytest.mark.parametrize("variable", ["discharge", "rainfall", "urban_drool"])
def test_make_source(offline_timeseries, sites, variable):

    src = single_variable.make_source(variable=variable, sites=sites,)
    assert len(src["site"].unique()) == len(sites), "sites must be stacked"
    assert len(src) == len(sites) * 5  # same as count in monkeypatch
    assert len(src["variable"].unique()) == 1, "only one variable allowed"


@pytest.mark.integration
@pytest.mark.parametrize("variable", ["discharge", "rainfall"])
def test_hydstra_integration_make_source(variable):

    src = single_variable.make_source(
        variable=variable,
        start_date="2014-01-01",
        end_date="2015-01-01",
        sites=["ALISO_JERONIMO"],
        intervals=["month"],
        agg_methods=["mean"],
    )

    assert len(src["variable"].unique()) == 1, "only one variable allowed"


@pytest.mark.integration
@pytest.mark.parametrize("sites", [["4"], ["4", "8"]])
@pytest.mark.parametrize(
    "trace_upstreams", [[False], [False, True], [True], [True, True]]
)
def test_dt_metrics_integration_make_source(sites, trace_upstreams):

    kwargs = dict(
        variable="urban_drool",
        start_date="2016-01-01",
        end_date="2018-01-01",
        sites=sites,
        intervals=["month"],
        agg_methods=["sum"],
        trace_upstreams=trace_upstreams,
    )

    # if len(sites) < len(trace_upstreams):
    #     with pytest.raises()

    src = single_variable.make_source(**kwargs)

    assert len(src["variable"].unique()) == 1, "only one variable allowed"
    assert len(src["site"].unique()) == len(sites), "all sites must be included."


def test_make_plot():
    pass


def test_dispatch():
    pass
