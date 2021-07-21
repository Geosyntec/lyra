from fastapi import APIRouter, Depends

from lyra.api.endpoints import (
    admin,
    bg_tasks,
    deprecated,
    dt_metrics,
    hydstra,
    plot,
    rsb,
    spatial,
    tasks,
    test,
)
from lyra.core.security import authenticate_admin_access

api_router = APIRouter()

# priority routes
api_router.include_router(plot.router, prefix="/plot", tags=["plot"])
api_router.include_router(spatial.router, prefix="/spatial", tags=["spatial"])
api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["tasks", "jobs", "drooltool", "hydstra", "plot", "rsb"],
)


# debug and util routes
api_router.include_router(dt_metrics.router, prefix="/dt_metrics", tags=["drooltool"])
api_router.include_router(hydstra.router, prefix="/hydstra", tags=["hydstra"])
api_router.include_router(rsb.router, prefix="/regional_subbasins", tags=["rsb"])


# admin only routes
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["auth", "admin"],
    dependencies=[Depends(authenticate_admin_access)],
)
api_router.include_router(
    bg_tasks.router,
    prefix="/bg_tasks",
    tags=["auth", "admin", "jobs"],
    dependencies=[Depends(authenticate_admin_access)],
)

api_router.include_router(test.router, prefix="/test")
api_router.include_router(deprecated.router, prefix="/plot", tags=["deprecated"])
