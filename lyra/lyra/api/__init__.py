from fastapi import APIRouter

from lyra.api.endpoints import hydstra, plot


api_router = APIRouter()
api_router.include_router(hydstra.router, prefix="/hydstra")
api_router.include_router(plot.router, prefix="/plot")
