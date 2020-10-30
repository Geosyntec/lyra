from fastapi import APIRouter

from lyra.site.views import main

site_router = APIRouter()
site_router.include_router(main.router)
