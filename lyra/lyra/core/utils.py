from typing import Optional

from celery.task import Task
from fastapi import APIRouter

from lyra.core.config import settings
from lyra.models.response_models import (
    CeleryTaskJSONResponse,
    ForegroundTaskJSONResponse,
)


def run_task(
    task: Task,
    router: APIRouter,
    get_route: str,
    force_foreground: Optional[bool] = False,
):
    if force_foreground or settings.FORCE_FOREGROUND:
        return ForegroundTaskJSONResponse(data=task())

    else:
        task = task.apply_async()
        router_path = router.url_path_for(get_route, task_id=task.id)
        result_route = f"api{router_path}"

        return CeleryTaskJSONResponse(
            data=task.result,
            status=task.status,
            task_id=task.id,
            result_route=result_route,
        )
