import pytest


@pytest.mark.integration
@pytest.mark.parametrize(
    "route, ",
    [
        '/api/plot/multi_variable?f=json&timeseries=[{"site":"ALISO_STP","variable":"discharge"}]',
        (
            "/api/plot/multi_variable?f=json&timeseries=["
            '{"site":"ALISO_STP","variable":"discharge"},'
            '{"site":"ALISO_JERONIMO","variable":"discharge"}'
            "]"
        ),
        (
            "/api/plot/multi_variable?f=json&start_date=2020-03-01&timeseries=["
            '{"site":"ALISO_STP","variable":"urban_drool"},'
            '{"site":"ALISO_JERONIMO","variable":"discharge"}'
            "]"
        ),
        (
            "/api/plot/multi_variable?f=json&start_date=2020-03-01&timeseries=["
            '{"site":"ALISO_STP","variable":"discharge"},'
            '{"site":"ALISO_JERONIMO","variable":"urban_drool"}'
            "]"
        ),
    ],
)
def test_multi_variable_spec_integration(client, route):

    get_response = client.get(route)
    assert get_response.status_code == 200, get_response.content

    rjson = get_response.json()
    assert rjson["status"].lower() == "success", rjson

    spec = rjson["data"]["spec"]
    assert spec is not None, rjson


example_routes = [
    # different input variables create two plots
    '/api/plot/multi_variable?f=html&end_date=2021-06-01&timeseries=[{"site":"ALISO_STP","variable":"discharge","interval":"day"},{"site":"ALISO_JERONIMO","variable":"rainfall","interval":"day"}]',
    # same input variables are created on one plot
    '/api/plot/multi_variable?f=html&end_date=2021-06-01&timeseries=[{"site":"ALISO_STP","variable":"discharge","interval":"day"},{"site":"ALISO_JERONIMO","variable":"discharge","interval":"day"}]',
    # all combos are supported
    '/api/plot/multi_variable?f=html&end_date=2021-06-01&timeseries=[{"site":"ALISO_STP","variable":"discharge","interval":"day"},{"site":"ALISO_JERONIMO","variable":"discharge","interval":"day"},{"site":"ALISO_JERONIMO","variable":"rainfall","interval":"day"}]',
    # all combos are supported
    '/api/plot/multi_variable?f=html&end_date=2021-06-01&timeseries=[{"site":"ALISO_JERONIMO","variable":"rainfall","interval":"day"},{"site":"ALISO_STP","variable":"discharge","interval":"day"},{"site":"ALISO_JERONIMO","variable":"discharge","interval":"day"}]',
    # dry weather vs wet weather
    '/api/plot/multi_variable?f=html&json={"interval":"day","timeseries":[{"site":"J03_9216_1","variable":"rainfall"},{"site":"J03_9216_1","variable":"discharge","weather_condition":"wet"},{"site":"J03_9216_1","variable":"discharge","weather_condition":"dry"}]}',
]
