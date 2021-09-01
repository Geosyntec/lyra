from typing import Dict

from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

from lyra.api.requests import LyraRoute
from lyra.core.config import cfg


router = APIRouter(route_class=LyraRoute, default_response_class=ORJSONResponse)


@router.get("/variables")
def get_variables() -> Dict:
    return cfg.get("variables", {})
