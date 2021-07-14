from typing import Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse

from lyra.models.request_models import SpatialResponseFormat

router = APIRouter()


@router.get("/site_info")
async def get_swn_site_info():
    return FileResponse("lyra/data/mount/swn/hydstra/swn_sites.json")


@router.get("/regional_subbasins")
async def get_rsb_geojson(
    f: Optional[SpatialResponseFormat] = SpatialResponseFormat.topojson,
) -> FileResponse:
    path = "lyra/data/mount/swn/mnwd/drooltool/spatial/"
    file = "rsb_topo_4326_latest.json"
    if f == "geojson":
        file = "rsb_geo_4326_latest.json"

    return FileResponse(path + file)
