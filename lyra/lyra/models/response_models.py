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


class ResponseFormat(str, Enum):
    json = "json"
    geojson = "geojson"
    topojson = "topojson"
    html = "html"


class SpatialResponseFormat(str, Enum):
    geojson = "geojson"
    topojson = "topojson"


class DataResponseFormat(str, Enum):
    json = "json"
    html = "html"


class ChartData(BaseModel):
    spec: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class ChartJSONResponse(JSONAPIResponse):
    data: ChartData
