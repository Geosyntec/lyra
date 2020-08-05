from fastapi import APIRouter

from lyra.site.views.main import router as main


site_router = APIRouter()
site_router.include_router(main)
