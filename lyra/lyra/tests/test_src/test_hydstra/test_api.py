import pytest

from lyra.core import async_requests
from lyra.src.hydstra import api


@pytest.fixture
def mock_get_site_list(monkeypatch):
    async def _get_site_list(*args, **kwargs):
        return {"_return": {"sites": ["somelist"]}}

    monkeypatch.setattr(async_requests, "send_request", _get_site_list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hydstra_get_site_list_integration():
    rsp = await api.get_site_list()
    assert "sites" in rsp["_return"]


@pytest.mark.asyncio
async def test_hydstra_get_site_list(mock_get_site_list):
    rsp = await api.get_site_list()
    assert "sites" in rsp["_return"]


@pytest.fixture
def mock_get_sites_db_info(monkeypatch):
    async def _get_sites_db_info(*args, **kwargs):
        return {"_return": {"rows": [{"station": "ELTORO"}]}}

    monkeypatch.setattr(async_requests, "send_request", _get_sites_db_info)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("site", [None, "ELTORO"])
async def test_hydstra_get_sites_db_info_integration(site):
    rsp = await api.get_sites_db_info(site=site)
    if site is None:
        assert len(rsp["_return"]["rows"]) > 20, "there should be a lot of these"
    else:
        assert (
            rsp["_return"]["rows"][0]["station"] == site
        ), "this should filter to the requested site"


@pytest.mark.asyncio
async def test_hydstra_get_sites_db_info(mock_get_sites_db_info):
    rsp = await api.get_sites_db_info(site="ELTORO")
    assert rsp["_return"]["rows"][0]["station"] == "ELTORO"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("site", [None, "ELTORO"])
async def test_hydstra_get_site_db_info_integration(site):
    rsp = await api.get_site_db_info(site=site)
    if site is None:
        assert (
            len(rsp["_return"]["rows"]) == 0
        ), "'None' is not a valid site filter, so empty return."
    else:
        assert (
            rsp["_return"]["rows"][0]["station"] == site
        ), "this should filter to the requested site"


@pytest.mark.asyncio
async def test_hydstra_get_site_db_info(
    mock_get_sites_db_info,  # it's ok to use same mock object
):
    rsp = await api.get_site_db_info(site="ELTORO")
    assert rsp["_return"]["rows"][0]["station"] == "ELTORO"


@pytest.fixture
def mock_get_site_geojson(monkeypatch):
    async def _get_site_geojson(*args, **kwargs):
        return {"_return": {"features": ["some list of feature"]}}

    monkeypatch.setattr(async_requests, "send_request", _get_site_geojson)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("site_list", [None, ["ELTORO"]])
async def test_hydstra_get_site_geojson_integration(site_list):
    rsp = await api.get_site_geojson(site_list=site_list)
    if site_list is None:
        assert len(rsp["_return"]["features"]) > 20, "there should be a lot of these"
    else:
        assert len(rsp["_return"]["features"]) == len(
            site_list
        ), "this should filter to the requested site"


@pytest.mark.asyncio
async def test_hydstra_get_site_geojson(mock_get_site_geojson):
    rsp = await api.get_site_geojson(site_list=["site_list"])
    assert len(rsp["_return"]["features"]) == 1


@pytest.fixture
def mock_get_trace(monkeypatch):
    async def _get_trace(*args, **kwargs):
        return {"_return": {"traces": ["some list of traces"]}}

    monkeypatch.setattr(async_requests, "send_request", _get_trace)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hydstra_get_trace_integration():
    rsp = await api.get_trace(
        site_list=["ELTORO"],
        var_list=["11"],
        start_time="20100101000000",
        end_time="20200101000000",
        interval="year",
        data_type="tot",
        datasource="PUBLISH",
    )

    assert len(rsp["_return"]["traces"]) == 1


@pytest.mark.asyncio
async def test_hydstra_get_trace(mock_get_trace):
    rsp = await api.get_trace(
        site_list=["ELTORO"],
        var_list=["11"],
        start_time="20100101000000",
        end_time="20200101000000",
        interval="year",
        data_type="tot",
        datasource="PUBLISH",
    )

    assert len(rsp["_return"]["traces"]) == 1
