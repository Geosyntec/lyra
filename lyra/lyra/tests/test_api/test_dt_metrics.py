from copy import deepcopy

import pytest

from lyra.connections import database
from lyra.core import config, security


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
        "api/dt_metrics?catchidns=4&years=2016&variables=overall_MeterID_count&force_foreground=true"
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("errors"), f"should have errors since we aren't authorized.\n{data}"


@pytest.mark.integration
def test_dt_metrics_no_cache_engine(monkeypatch, client_no_cache, data_engine):
    client = client_no_cache

    monkeypatch.setattr(database, "engine", data_engine)
    client.app.dependency_overrides[security.is_admin] = lambda: True
    response = client.get(
        "api/dt_metrics?catchidns=199&years=2015&months=1&variables=overall_MeterID_count&force_foreground=true"
    )
    client.app.dependency_overrides.pop(security.is_admin)
    assert response.status_code == 200
    data = response.json().get("data", [])
    assert len(data) == 1

    row = data[0]
    exp = {
        "catchidn": 199,
        "year": 2015,
        "month": 1,
        "variable": "overall_MeterID_count",
        "value": 102.0,
    }

    for k, v in exp.items():
        assert row[k] == v


@pytest.mark.integration
def test_dt_metrics_no_cache_engine_no_admin(
    monkeypatch, client_no_cache_foreground, data_engine
):
    client = client_no_cache_foreground
    monkeypatch.setattr(database, "engine", data_engine)

    response = client.get(
        "api/dt_metrics?catchidns=199&years=2015&months=1&variables=overall_MeterID_count"
    )
    assert response.status_code == 200
    data = response.json().get("data", [])
    assert len(data) == 1, response.json()

    row = data[0]
    exp = {
        "catchidn": 199,
        "year": 2015,
        "month": 1,
        "variable": "overall_MeterID_count",
        "value": 102.0,
    }

    for k, v in exp.items():
        assert row[k] == v
