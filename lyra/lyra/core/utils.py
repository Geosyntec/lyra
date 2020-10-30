import asyncio
import itertools
from typing import Any, Dict, List, Optional, Union

import pandas
from celery.canvas import Signature
from celery.result import AsyncResult
from fastapi import Depends, Query, Request

from lyra.core import security
from lyra.models.response_models import (
    CeleryTaskJSONResponse,
    ForegroundTaskJSONResponse,
    JSONAPIResponse,
    RawJSONResponse,
)


async def wait_a_sec_and_see_if_we_can_return_some_data(
    task: AsyncResult, timeout: Optional[float] = None
) -> None:
    if timeout is None:
        timeout = 0.1

    _max_timeout = 120  # seconds
    timeout = min(timeout, _max_timeout)  # prevent long timeout requests.

    t = 0.0
    inc = 0.05  # check back every inc seconds
    while t < timeout:
        if task.ready():  # exit even if the task failed
            return
        else:
            t += inc
            await asyncio.sleep(inc)
    return


def run_task_kwargs(
    request: Request,
    force_foreground: Optional[bool] = Query(
        None, description="requires admin authentication else has no effect"
    ),
    timeout: Optional[float] = Query(
        None, description="serverside async polling up to 10 seconds"
    ),
    is_admininstrator: bool = Depends(security.is_admin),
) -> Dict[str, Any]:

    rsp: Dict = dict(request=request)
    auth_msg = []

    rsp["force_foreground"] = request.app.settings.FORCE_FOREGROUND

    if force_foreground is not None:
        if is_admininstrator:
            rsp["force_foreground"] = force_foreground
        else:
            auth_msg.append(
                "Argument Ignored Error: User not authenticated for arg `force_foreground`"
            )

    # allow timeout to simplify API polling requirements. Max timeout is set in the
    # wait and see function above.
    rsp["timeout"] = timeout

    if auth_msg:
        rsp["errors"] = auth_msg

    return rsp


async def run_task(
    task: Union[Signature, AsyncResult],
    get_route: Optional[str] = None,
    request: Optional[Request] = None,
    force_foreground: Optional[bool] = False,
    timeout: Optional[float] = None,
    errors: Optional[List[str]] = None,
) -> JSONAPIResponse:

    if force_foreground:
        result = task()
        if isinstance(result, str):  # return the response directly.
            return RawJSONResponse(result.encode())  # type: ignore
        else:
            return ForegroundTaskJSONResponse(data=result, errors=errors)

    else:
        result = None
        if isinstance(task, Signature):
            task = task.apply_async()

            _ = await wait_a_sec_and_see_if_we_can_return_some_data(
                task, timeout=timeout
            )

        if request:
            result_route = str(request.url)
            if get_route:
                result_route = str(request.url_for(get_route, task_id=task.id))
        else:
            result_route = task.id
            if get_route:
                result_route = get_route

        if task.successful():
            result = task.result
            if isinstance(result, str):  # return the response directly.
                return RawJSONResponse(result.encode())  # type: ignore

        return CeleryTaskJSONResponse(
            data=result,
            status=task.status,
            task_id=task.id,
            result_route=result_route,
            errors=errors,
        )


def to_categorical_lookup(df, variable):
    cat = pandas.Categorical(df[variable])
    df[variable] = cat.codes
    return (
        df,
        pandas.DataFrame(
            {"variable": range(len(cat.categories)), "variable_name": cat.categories}
        ),
    )


def infer_freq(index):
    """If no frequency, use min difference in index timestamp to guess.

    Parameters
    ----------
    index : pandas.Series.index or pandas.DataFrame.index

    """
    if not index.is_all_dates:
        raise ValueError("must be a datetime index")

    freq = pandas.infer_freq(index)
    if freq is None:
        freq = index.to_series().diff().min()
    return freq


def flatten_expand_list(ls: List[str]) -> List[str]:
    return list(itertools.chain.from_iterable([s.split(",") for s in ls]))
