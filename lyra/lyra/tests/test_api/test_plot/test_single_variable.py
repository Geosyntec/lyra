import pytest


@pytest.mark.integration
@pytest.mark.parametrize(
    "route, exp_spec_keys",
    [
        (
            "/api/plot/single_variable?f=json&variable=urban_drool&start_date=2015-01-01&end_date=2015-04-01&sites=4",
            ["$schema", "layer"],
        ),
        (
            "/api/plot/single_variable?f=json&variable=urban_drool&start_date=2015-01-01&end_date=2015-04-01&sites=4&sites=8",
            ["$schema", "layer"],
        ),
    ],
)
def test_single_variable_spec_integration(client, route, exp_spec_keys):

    get_response = client.get(route)
    assert get_response.status_code == 200

    rjson = get_response.json()
    assert rjson["status"].lower() == "success"

    spec = rjson["data"]["spec"]
    assert all(i in spec for i in exp_spec_keys)


@pytest.mark.parametrize(
    "route, exp_spec_keys",
    [
        (
            "/api/plot/single_variable?f=json&variable=urban_drool&start_date=2015-01-01&end_date=2015-04-01&sites=4",
            ["$schema", "layer"],
        ),
        (
            "/api/plot/single_variable?f=json&variable=urban_drool&start_date=2015-01-01&end_date=2015-04-01&sites=4&sites=8",
            ["$schema", "layer"],
        ),
    ],
)
def test_single_variable_spec(client, route, exp_spec_keys):

    get_response = client.get(route)
    assert get_response.status_code == 200

    rjson = get_response.json()
    assert rjson["status"].lower() == "success"

    spec = rjson["data"]["spec"]
    assert all(i in spec for i in exp_spec_keys)


@pytest.mark.integration
@pytest.mark.parametrize(
    "route",
    [
        "/api/plot/single_variable/data?{f}&variable=urban_drool&start_date=2015-01-01&end_date=2015-04-01&sites=4",
        "/api/plot/single_variable/data?{f}&variable=discharge&start_date=2015-01-01&end_date=2015-04-01&sites=ALISO_STP",
    ],
)
@pytest.mark.parametrize("f", ["", "f=json", "f=csv"])
def test_single_variable_data(client, route, f):

    route = route.format(f=f)

    get_response = client.get(route)
    assert get_response.status_code == 200
    assert len(get_response.content) > 100
