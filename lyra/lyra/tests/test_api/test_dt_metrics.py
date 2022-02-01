import pytest

from lyra.connections import database
from lyra.core import security


@pytest.mark.integration
def test_dt_metrics(client_no_cache):
    client = client_no_cache
    client.app.dependency_overrides[security.is_admin] = lambda: True
    response = client.get(
        "api/dt_metrics?catchidns=8&years=2016&variables=overall_MeterID_count&force_foreground=true"
    )
    client.app.dependency_overrides.pop(security.is_admin)
    assert response.status_code == 200
    data = response.json().get("data")

    assert (
        len(data) == 12
    ), "should be 1 year of monthly data for 1 variable and at 1 site."


@pytest.mark.integration
def test_dt_metrics_no_cache(client_no_cache):
    client = client_no_cache
    response = client.get(
        "api/dt_metrics?years=2016&variables=overall_MeterID_count&force_foreground=true"
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("errors"), f"should have errors since we aren't authorized.\n{data}"


@pytest.mark.skip
@pytest.mark.integration
def test_dt_metrics_no_cache_engine(monkeypatch, client_no_cache, data_engine):
    client = client_no_cache

    monkeypatch.setattr(database, "engine", data_engine)
    client.app.dependency_overrides[security.is_admin] = lambda: True
    response = client.get(
        "api/dt_metrics?years=2016&months=1&variables=overall_MeterID_count&force_foreground=true"
    )
    client.app.dependency_overrides.pop(security.is_admin)
    assert response.status_code == 200, response.status_code
    data = response.json().get("data", [])
    assert len(data), response.json()


@pytest.mark.skip
@pytest.mark.integration
def test_dt_metrics_no_cache_engine_no_admin(
    monkeypatch, client_no_cache_foreground, data_engine
):
    client = client_no_cache_foreground
    monkeypatch.setattr(database, "engine", data_engine)

    response = client.get(
        "api/dt_metrics?years=2016&months=1&variables=overall_MeterID_count"
    )
    assert response.status_code == 200
    data = response.json().get("data", [])
    assert len(data), response.json()
