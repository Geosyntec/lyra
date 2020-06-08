from fastapi import APIRouter

from lyra.home.views.main import router as main


home_router = APIRouter()
home_router.include_router(main)
