import pytest

from lyra.src.hydstra import tasks


@pytest.mark.asyncio
async def test_hydstra_get_site_geojson_info():

    geo_info = await tasks.get_site_geojson_info()

    assert len(geo_info), "empty dataframe"
    assert len(geo_info.geometry), "not a geodataframe"
