import pydantic
import pytest

from lyra.models import plot_models


@pytest.mark.parametrize(
    "bad_input",
    [
        {"variable": "drool_tool", "sites": ["4"]},  # bad var
        {"variable": "urban_drool", "sites": ["ELTORO,"]},  # bad site
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
            "sites": ["4"],
            "intervals": ["year"],
            "agg_methods": ["sum"],
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
