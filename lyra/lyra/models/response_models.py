from typing import Any, Optional
from typing_extensions import Literal

from pydantic import BaseModel


class JSONAPIResponse(BaseModel):
    status: str = "SUCCESS"
    data: Optional[Any] = None


class ForegroundTaskJSONResponse(JSONAPIResponse):
    process_type: str = "foreground_process"


class CeleryTaskJSONResponse(JSONAPIResponse):
    process_type: str = "celery_async_process"
    task_id: Optional[str] = None
    result_route: Optional[str] = None


class HydstraJSONResponse(JSONAPIResponse):
    process_type: str = "hydstra_api_request"


class CachedJSONResponse(JSONAPIResponse):
    process_type: str = "cached_result"
    expires_after: int  # expressed in seconds
