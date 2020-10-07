from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse

import lyra.bg_worker as bg
from lyra.core.utils import run_task, run_task_kwargs
from lyra.models.response_models import JSONAPIResponse

router = APIRouter(default_response_class=ORJSONResponse)

## This task has no effect when run on dev or on prod; only local where volumes are shared. v0.1.16
# @router.post("/build_static_references", response_model=RunTaskResponse)
# async def post_build_static_references(
#     kwargs: dict = Depends(run_task_kwargs),
# ) -> Dict[str, Any]:
#     task = bg.background_build_static_references.s()
#     return await run_task(task, get_route="get_build_static_references", **kwargs)


# @router.get("/build_static_references/{task_id}", response_model=RunTaskResponse)
# async def get_build_static_references(
#     task_id: str, kwargs: dict = Depends(run_task_kwargs)
# ) -> Dict[str, Any]:
#     task = bg.background_build_static_references.AsyncResult(task_id, app=router)
#     return await run_task(task, **kwargs)


@router.get("/update_drooltool_database", response_model=JSONAPIResponse)
async def update_drooltool_database(
    update: bool = True, kwargs: dict = Depends(run_task_kwargs),
) -> JSONAPIResponse:
    task = bg.background_update_drooltool_database.s(update=update)
    return await run_task(task, get_route="get_task", **kwargs)


# @router.get("/update_drooltool_database/{task_id}", response_model=RunTaskResponse)
# async def get_update_drooltool_database(
#     task_id: str, kwargs: dict = Depends(run_task_kwargs)
# ) -> Dict[str, Any]:
#     task = bg.background_update_drooltool_database.AsyncResult(task_id, app=router)
#     return await run_task(task, **kwargs)


@router.get("/update_rsb_geojson", response_model=JSONAPIResponse)
async def update_rsb_geojson(
    kwargs: dict = Depends(run_task_kwargs),
) -> JSONAPIResponse:
    task = bg.background_update_rsb_geojson.s()
    return await run_task(task, get_route="get_task", **kwargs)


@router.get("/refresh_cache", response_model=JSONAPIResponse)
async def refresh_cache(kwargs: dict = Depends(run_task_kwargs)) -> JSONAPIResponse:
    task = bg.background_refresh_cache.s()
    return await run_task(task, get_route="get_task", **kwargs)


# @router.get("/update_rsb_geojson/{task_id}", response_model=RunTaskResponse)
# async def get_update_rsb_geojson(
#     task_id: str, kwargs: dict = Depends(run_task_kwargs)
# ) -> Dict[str, Any]:
#     task = bg.background_update_rsb_geojson.AsyncResult(task_id, app=router)
#     return await run_task(task, **kwargs)


# -------Nothing------------------


# @router.post("/sleep/", response_model=JSONAPIResponse)
# async def post_run_sleep_in_background(
#     duration: float, kwargs: dict = Depends(run_task_kwargs)
# ) -> Dict[str, Any]:
#     task = bg.background_run_sleep_in_background.s(duration=duration)
#     return await run_task(task, get_route="get_run_sleep_in_background", **kwargs)


# @router.get("/sleep/{task_id}", response_model=JSONAPIResponse)
# async def get_run_sleep_in_background(
#     task_id: str, kwargs: dict = Depends(run_task_kwargs)
# ) -> Dict[str, Any]:
#     task = bg.background_run_sleep_in_background.AsyncResult(task_id, app=router)
#     return await run_task(task, **kwargs)


# @router.post("/sleep_cached/", response_model=JSONAPIResponse)
# async def post_run_sleep_in_background_cached(
#     duration: float, kwargs: dict = Depends(run_task_kwargs)
# ) -> Dict[str, Any]:
#     task = bg.background_run_sleep_in_background_cached.s(duration=duration)
#     return await run_task(task, **kwargs)


# @router.get("/sleep_cached/{task_id}", response_model=JSONAPIResponse)
# async def get_run_sleep_in_background_cached(
#     task_id: str, kwargs: dict = Depends(run_task_kwargs)
# ) -> Dict[str, Any]:
#     task = bg.background_run_sleep_in_background_cached.AsyncResult(task_id, app=router)
#     return await run_task(task, **kwargs)
