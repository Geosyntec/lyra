from fastapi import APIRouter

from lyra.api.endpoints.hydstra import router as hydstra


api_router = APIRouter()
api_router.include_router(hydstra)
