from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.staticfiles import StaticFiles


def create_app(settings_override: Optional[Dict[str, Any]] = None) -> FastAPI:

    from lyra.api import api_router
    from lyra.core.config import settings
    from lyra.site import site_router

    _settings = settings.copy()

    if settings_override is not None:
        _settings.update(settings_override)

    app = FastAPI(
        title="lyra", version=_settings.VERSION, docs_url=None, redoc_url=None
    )

    setattr(app, "settings", _settings)

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=str(app.openapi_url),
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_favicon_url="/static/logo/lyra_logo_icon.ico",
        )

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=str(app.openapi_url),
            title=app.title + " - ReDoc",
            redoc_favicon_url="/static/logo/lyra_logo_icon.ico",
        )

    app.include_router(api_router, prefix="/api")
    app.include_router(site_router)

    app.mount("/static", StaticFiles(directory="lyra/static"), name="static")
    app.mount(
        "/site/static", StaticFiles(directory="lyra/site/static"), name="site/static"
    )

    app.mount("/data", StaticFiles(directory="lyra/data"), name="data")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.ALLOW_CORS_ORIGINS,
        allow_origin_regex=_settings.ALLOW_CORS_ORIGIN_REGEX,
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS", "POST"],
        allow_headers=["*"],
    )

    return app
