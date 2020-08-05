from typing import Any, Dict, Optional, Union
import asyncio

from celery.canvas import Signature
from celery.exceptions import TimeoutError
from celery.result import AsyncResult
from fastapi import APIRouter, Request
import pandas

from lyra.core.config import settings
from lyra.models.response_models import (
    CeleryTaskJSONResponse,
    ForegroundTaskJSONResponse,
)


async def wait_a_sec_and_see_if_we_can_return_some_data(
    task: AsyncResult, timeout: float = 0.2, inc: float = 0.05
) -> Optional[Dict[str, Any]]:
    t = 0
    while t < timeout:
        if task.successful():
            return
        else:
            t += inc
            await asyncio.sleep(inc)


def run_task_kwargs(
    request: Request, force_foreground: Optional[bool] = None, timeout: float = 0.2
):
    if force_foreground is None:
        force_foreground = settings.FORCE_FOREGROUND
    return dict(request=request, force_foreground=force_foreground, timeout=timeout)


async def run_task(
    task: Union[Signature, AsyncResult],
    get_route: Optional[str] = None,
    request: Optional[Request] = None,
    force_foreground: Optional[bool] = False,
    timeout: float = 0.2,
):

    if force_foreground:
        return ForegroundTaskJSONResponse(data=task())

    else:
        result = None
        if isinstance(task, Signature):
            task = task.apply_async()

            _ = await wait_a_sec_and_see_if_we_can_return_some_data(
                task, timeout=timeout
            )

        if task.successful():
            result = task.result

        if request:
            result_route = str(request.url)
            if get_route:
                result_route = str(request.url_for(get_route, task_id=task.id))
        else:
            result_route = task.id
            if get_route:
                result_route = get_route

        return CeleryTaskJSONResponse(
            data=result, status=task.status, task_id=task.id, result_route=result_route,
        )


def to_categorical_lookup(df, variable):
    cat = pandas.Categorical(df[variable])
    df[variable] = cat.codes
    return df, pandas.DataFrame({variable: cat.categories})
