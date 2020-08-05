from typing import Any, Optional, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import lyra


def create_app(settings_override: Optional[Dict[str, Any]] = None):
    app = FastAPI(title="lyra", version=lyra.__version__)

    from lyra.api import api_router
    from lyra.site import site_router
    from lyra.core.config import settings

    app.include_router(api_router, prefix="/api")
    app.include_router(site_router)

    app.mount("/static", StaticFiles(directory="lyra/static"), name="static")
    app.mount(
        "/site/static", StaticFiles(directory="lyra/site/static"), name="site/static"
    )

    app.settings = settings
    if settings_override is not None:
        app.settings.update(settings_override)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app.settings.ALLOW_CORS_ORIGINS,
        allow_origin_regex=app.settings.ALLOW_CORS_ORIGIN_REGEX,
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS", "POST"],
        allow_headers=["*"],
    )

    return app
