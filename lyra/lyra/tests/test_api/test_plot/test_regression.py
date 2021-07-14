import pytest


@pytest.mark.integration
@pytest.mark.parametrize("regression_method", ["linear", "exp"])
@pytest.mark.parametrize(
    "route",
    [
        (
            "/api/plot/regression?f=json&timeseries=["
            '{"site":"ALISO_STP","variable":"discharge"},'
            '{"site":"ALISO_JERONIMO","variable":"discharge"}'
            "]"
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


"""
