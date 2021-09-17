import pytest


@pytest.mark.integration
@pytest.mark.parametrize("regression_method", ["linear", "exp"])
@pytest.mark.parametrize(
    "route",
    [
        (
            '/api/plot/regression?f=json&timeseries=[{"site":"ALISO_STP","variable":"discharge"},{"site":"ALISO_JERONIMO","variable":"discharge"}]'
        ),
        (
            "/api/plot/regression?f=json&timeseries=["
            '{"site":"ALISO_STP","variable":"urban_drool"},'
            '{"site":"ALISO_JERONIMO","variable":"discharge"}'
            "]"
        ),
    ],
)
def test_regression_spec_integration(client, route, regression_method):

    get_response = client.get(route + f"&regression_method={regression_method}")
    assert get_response.status_code == 200

    rjson = get_response.json()
    assert rjson["status"].lower() == "success"

    spec = rjson["data"]["spec"]
    assert spec is not None


example_routes = """
    # regressions default to linear
    /api/plot/regression?f=html&end_date=2021-06-01&interval=day&timeseries=[{"site":"ALISO_STP","variable":"discharge"},{"site":"ALISO_JERONIMO","variable":"rainfall"}]
    
    #
    /api/plot/regression?f=html&start_date=2019-01-01&end_date=2021-06-01&interval=month&timeseries=[{"site":"ALISO_STP","variable":"discharge"},{"site":"ALISO_JERONIMO","variable":"discharge"}]
    
    # multiple regression methods are supported
    /api/plot/regression?f=html&regression_method=log&start_date=2019-01-01&end_date=2021-06-01&interval=month&timeseries=[{"site":"ALISO_STP","variable":"discharge"},{"site":"ALISO_JERONIMO","variable":"discharge"}]
    
    # works as json
    /api/plot/regression?f=html&json={"regression_method":"log","start_date":"2000-01-01","end_date":"2021-06-01","interval":"month","timeseries":[{"site":"ALISO_STP","variable":"discharge"},{"site":"ALISO_JERONIMO","variable":"discharge"}]}

# no data, shouldn't fail
api/plot/regression/data?f=csv&json={"start_date":"2021-04-01","end_date":"2021-09-16","interval":"day","weather_condition":"wet","regression_method":"linear","timeseries":[{"variable":"discharge","site":"ALISO_STP","aggregation_method":"mean"},{"variable":"rainfall","site":"ALISO_STP","aggregation_method":"tot"}]}
"""


@pytest.mark.parametrize("f", ("json", "html"))
@pytest.mark.parametrize("weather", ("wet", "dry", "both"))
@pytest.mark.parametrize(
    "route",
    [
        'api/plot/regression?f=%s&json={"start_date":"2021-04-01","end_date":"2021-09-16","interval":"day","weather_condition":"%s","regression_method":"linear","timeseries":[{"variable":"discharge","site":"ALISO_STP","aggregation_method":"mean"},{"variable":"rainfall","site":"ALISO_STP","aggregation_method":"tot"}]}',
    ],
)
def test_regression_should_not_fail(client, route, f, weather):
    route = route % (f, weather)
    get_response = client.get(route)
    assert get_response.status_code == 200


@pytest.mark.parametrize("f", ("json", "csv"))
@pytest.mark.parametrize("weather", ("wet", "dry", "both"))
@pytest.mark.parametrize(
    "route",
    [
        'api/plot/regression/data?f=%s&json={"start_date":"2021-04-01","end_date":"2021-09-16","interval":"day","weather_condition":"%s","regression_method":"linear","timeseries":[{"variable":"discharge","site":"ALISO_STP","aggregation_method":"mean"},{"variable":"rainfall","site":"ALISO_STP","aggregation_method":"tot"}]}',
    ],
)
def test_regression_data_should_not_fail(client, route, f, weather):
    route = route % (f, weather)
    get_response = client.get(route)
    assert get_response.status_code == 200
