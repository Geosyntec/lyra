import pytest


@pytest.mark.parametrize(
    "route",
    [
        "/",
        "/home",
        "/docs",
        "/redoc",
        "/test_cors",
        "/map",
        "/map?catchidns=4" "/timeseries",
        "/single_variable",
    ],
)
def test_site(client, route):
    response = client.get(route)
    assert response.status_code == 200
