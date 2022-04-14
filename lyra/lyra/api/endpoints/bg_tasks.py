from typing import Dict

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse

import lyra.bg_worker as bg
from lyra.core.utils import local_path, run_task, run_task_kwargs
from lyra.models.response_models import JSONAPIResponse

router = APIRouter(default_response_class=ORJSONResponse)


@router.get("/update_drooltool_database", response_model=JSONAPIResponse)
async def update_drooltool_database(
    update: bool = True, kwargs: dict = Depends(run_task_kwargs),
) -> JSONAPIResponse:  # pragma: no cover
    task = bg.background_update_drooltool_database.s(update=update)
    return await run_task(task, get_route="get_task", **kwargs)


@router.get("/update_rsb_geojson", response_model=JSONAPIResponse)
async def update_rsb_geojson(
    kwargs: dict = Depends(run_task_kwargs),
) -> JSONAPIResponse:  # pragma: no cover
    task = bg.background_update_rsb_geojson.s()
    return await run_task(task, get_route="get_task", **kwargs)


@router.get("/refresh_cache", response_model=JSONAPIResponse)
async def refresh_cache(
    kwargs: dict = Depends(run_task_kwargs),
) -> JSONAPIResponse:  # pragma: no cover
    task = bg.background_refresh_cache.s()
    return await run_task(task, get_route="get_task", **kwargs)


@router.get("/update_hydstra_site_info", response_model=JSONAPIResponse)
async def update_hydstra_site_info(
    kwargs: dict = Depends(run_task_kwargs),
) -> JSONAPIResponse:  # pragma: no cover
    task = bg.background_update_hydstra_site_info.s()
    return await run_task(task, get_route="get_task", **kwargs)


@router.get("/data_dir", response_model=JSONAPIResponse)
async def show_data_directory_contents() -> Dict:  # pragma: no cover
    response = {"data": list(local_path("data").glob("**/*"))}
    return response
