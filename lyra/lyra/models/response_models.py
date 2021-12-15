from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class RawJSONResponse(JSONResponse):
    def render(self, content: bytes) -> bytes:
        return content


class JSONAPIResponse(BaseModel):
    status: str = "SUCCESS"
    process_type: str = "foreground"
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    task_id: Optional[str] = None
    result_route: Optional[str] = None
    expires_after: Optional[int] = None
    request_time_seconds: Optional[float] = None
    hydstra_time_seconds: Optional[float] = None


class ForegroundTaskJSONResponse(JSONAPIResponse):
    process_type: str = "foreground"


class CeleryTaskJSONResponse(JSONAPIResponse):
    process_type: str = "async_background"
    task_id: str
    result_route: Optional[str] = None


class HydstraJSONResponse(JSONAPIResponse):
    process_type: str = "hydstra_request"


class CachedJSONResponse(JSONAPIResponse):
    process_type: str = "cached"
    expires_after: Optional[int] = None  # expressed in seconds
    ts: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ChartData(BaseModel):
    spec: Optional[Dict[str, Any]] = None
    messages: Optional[List[str]] = None
    table: Optional[Any] = None
    chart_status: str = "SUCCESS"


class ChartJSONResponse(JSONAPIResponse):
    data: ChartData
