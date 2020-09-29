from typing import Any, Dict
from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse

from lyra.core.celery_app import celery_app

from lyra.core.utils import run_task, run_task_kwargs
from lyra.models.response_models import JSONAPIResponse


router = APIRouter(default_response_class=ORJSONResponse)


@router.get(
    "/{task_id}", tags=["tasks"], response_model=JSONAPIResponse,
)
async def get_task(
    task_id: str, kwargs: dict = Depends(run_task_kwargs)
) -> Dict[str, Any]:
    task = celery_app.AsyncResult(task_id)
    return await run_task(task, **kwargs)
