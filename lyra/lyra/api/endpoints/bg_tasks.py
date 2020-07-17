from typing import Any, Dict
from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

import lyra.bg_worker as bg
from lyra.core.utils import run_task

router = APIRouter()


@router.post("/sleep/", response_class=ORJSONResponse)
async def post_run_sleep_in_background(duration: float) -> Dict[str, Any]:
    task = bg.background_run_sleep_in_background.s(duration=duration)
    return run_task(task, router=router, get_route="get_run_sleep_in_background")


@router.get("/sleep/{task_id}", response_class=ORJSONResponse)
async def get_run_sleep_in_background(task_id: str) -> Dict[str, Any]:
    task = bg.background_run_sleep_in_background.AsyncResult(task_id, app=router)
    return run_task(task)


@router.post("/sleep_cached/", response_class=ORJSONResponse)
async def post_run_sleep_in_background_cached(duration: float) -> Dict[str, Any]:
    task = bg.background_run_sleep_in_background_cached.s(duration=duration)
    return run_task(task, router=router, get_route="get_run_sleep_in_background")


@router.get("/sleep_cached/{task_id}", response_class=ORJSONResponse)
async def get_run_sleep_in_background_cached(task_id: str) -> Dict[str, Any]:
    task = bg.background_run_sleep_in_background_cached.AsyncResult(task_id, app=router)
    return run_task(task)
