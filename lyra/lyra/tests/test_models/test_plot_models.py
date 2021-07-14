import pydantic
import pytest

from lyra.models import plot_models


@pytest.mark.parametrize(
    "bad_input",
    [
        {"variable": "drool_tool", "sites": ["ALISO_STP"]},  # bad var
        {"variable": "urban_drool", "sites": ["ELTO&"]},  # bad site
        {
            "variable": "rainfall",
            "sites": ["ELTORO"],
            "intervals": ["month", "year"],  # count mismatch
        },
    ],
)
def test_single_var_raises(bad_input):
    pytest.raises(pydantic.ValidationError, plot_models.SingleVarSpec, **bad_input)


@pytest.mark.parametrize(
    "good_input",
    [
        {
            "variable": "urban_drool",
            "sites": ["ALISO_STP"],
            "intervals": ["year"],
            "agg_methods": ["tot"],
        },
        {"variable": "rainfall", "sites": ["ELTORO"], "intervals": ["year"]},
        {
            "variable": "rainfall",
            "sites": ["ELTORO", "LAGUNABEACH"],
            "intervals": ["month", "year"],
        },
    ],
)
def test_single_var(good_input):
    assert plot_models.SingleVarSpec(**good_input)


@pytest.mark.parametrize(
    "good_input",
    [
        {
            "variable": "urban_drool",
            "start_date": "2015-01-01",
            "site": "ALISO_STP",
            "interval": "year",
            "aggregation_method": "tot",
        },
        {
            "variable": "urban_drool",
            "start_date": "2015-05-01",
            "site": "ALISO_STP",
            "interval": "month",
            "aggregation_method": "tot",
        },
        {
            "variable": "discharge",
            "start_date": "2015-05-01",
            "site": "ALISO_STP",
            "interval": "day",
            "aggregation_method": "mean",
        },
        {
            "variable": "discharge",
            "start_date": "2015-05-01",
            "site": "ALISO_STP",
            "interval": "day",
            "aggregation_method": "tot",  # not possible for discharge but should be coerced to 'mean'
        },
    ],
)
def test_ts_schema(good_input):
    assert plot_models.TimeseriesSchema(**good_input)


@pytest.mark.parametrize(
    "bad_input",
    [
        {
            "variable": "urban_drool",
            "start_date": "2015-05-01",  # doesn't start jan 1
            "site": "ALISO_STP",
            "interval": "year",
            "aggregation_method": "tot",
        },
        {
            "variable": "urban_drool",
            "start_date": "2015-05-05",  # doesn't start on first of month
            "site": "ALISO_STP",
            "interval": "month",
            "aggregation_method": "tot",
        },
        {
            "variable": "rainfall",  # doestn't exist at this site
            "start_date": "2015-05-05",
            "site": "ALISO_STP",
            "interval": "day",
            "aggregation_method": "tot",
        },
    ],
)
def test_ts_schema_raises(bad_input):
    pytest.raises(pydantic.ValidationError, plot_models.TimeseriesSchema, **bad_input)


@pytest.mark.parametrize(
    "good_input",
    [
        {
            "start_date": "2020-01-01",
            "variable": "discharge",
            "timeseries": [{"site": "ALISO_STP"}, {"site": "ALISO_JERONIMO"}],
        },
        {
            "variable": "discharge",
            "timeseries": [{"site": "ALISO_STP"}, {"site": "ALISO_JERONIMO"}],
        },
        {
            "timeseries": [
                {"site": "ALISO_STP", "variable": "discharge",},
                {"site": "ALISO_JERONIMO", "variable": "discharge",},
            ],
        },
        {
            "start_date": "2020-01-01",
            "variable": "discharge",
            "bad_extra": "whatever",
            "timeseries": [{"site": "ALISO_STP"}, {"site": "ALISO_JERONIMO"}],
        },
    ],
)
def test_multi_var_broadcast(good_input):
    ts = plot_models.MultiVarSchema(**good_input).dict()["timeseries"]

    good_input.pop("timeseries", [])

    for k in good_input:
        for t in ts:
            if "bad" in k:
                assert k not in t
            else:
                assert t[k] == good_input[k]


@pytest.mark.parametrize(
    "bad_input",
    [
        {
            "start_date": "2020-01-01",
            "variable": "discharge",
            # missing timeseries key
        },
        # variable is a required key for timeseries
        {"timeseries": [{"site": "ALISO_STP"}, {"site": "ALISO_JERONIMO"}],},
        {
            # rainfall not available at stp
            "variable": "rainfall",
            "timeseries": [{"site": "ALISO_STP"}, {"site": "ALISO_JERONIMO"}],
        },
    ],
)
def test_multi_var_raises(bad_input):
    pytest.raises(pydantic.ValidationError, plot_models.MultiVarSchema, **bad_input)


@pytest.mark.parametrize(
    "bad_input",
    [
        {
            # two timeseries only
            "timeseries": [
                {"site": "ALISO_STP", "variable": "discharge"},
                {"site": "ALISO_JERONIMO", "variable": "discharge"},
                {"site": "ELTORO", "variable": "rainfall"},
            ],
        },
        {
            "variable": "discharge",
            "regression_method": "test",  # method dne
            "timeseries": [{"site": "ALISO_STP"}, {"site": "ALISO_JERONIMO"}],
        },
    ],
)
def test_regression_raises(bad_input):
    pytest.raises(pydantic.ValidationError, plot_models.RegressionSchema, **bad_input)
