from fastapi import APIRouter, Depends

from lyra.api.endpoints import admin, bg_tasks, dt_metrics, hydstra, plot, rsb, tasks
from lyra.core.security import authenticate_admin_access


api_router = APIRouter()
api_router.include_router(admin.router, prefix="/admin", tags=["auth", "admin"])
api_router.include_router(
    bg_tasks.router,
    prefix="/bg_tasks",
    tags=["auth", "jobs"],
    dependencies=[Depends(authenticate_admin_access)],
)
api_router.include_router(dt_metrics.router, prefix="/dt_metrics", tags=["drooltool"])
api_router.include_router(hydstra.router, prefix="/hydstra", tags=["hydstra"])
api_router.include_router(plot.router, prefix="/plot", tags=["plot"])
api_router.include_router(rsb.router, prefix="/regional_subbasins", tags=["rsb"])
api_router.include_router(
    tasks.router, prefix="/tasks", tags=["jobs", "drooltool", "hydstra", "plot", "rsb"]
)
