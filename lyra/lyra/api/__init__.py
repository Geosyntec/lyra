from fastapi import APIRouter

from lyra.api.endpoints import hydstra, plot, bg_tasks


api_router = APIRouter()
api_router.include_router(hydstra.router, prefix="/hydstra")
api_router.include_router(plot.router, prefix="/plot")
api_router.include_router(bg_tasks.router, prefix="/bg_tasks")
