from fastapi import APIRouter, Depends

from lyra.api.endpoints import admin, bg_tasks, hydstra, mnwd, plot
from lyra.api.security import authenticate_admin_access


api_router = APIRouter()
api_router.include_router(admin.router, prefix="/admin", tags=["auth"])
api_router.include_router(
    bg_tasks.router,
    prefix="/bg_tasks",
    tags=["auth", "jobs"],
    dependencies=[Depends(authenticate_admin_access)],
)
api_router.include_router(hydstra.router, prefix="/hydstra", tags=["hydstra"])
api_router.include_router(mnwd.router, prefix="/mnwd")
api_router.include_router(plot.router, prefix="/plot", tags=["plot"])
