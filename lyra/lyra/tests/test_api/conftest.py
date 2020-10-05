import pytest
from fastapi.testclient import TestClient

from lyra.core import cache
from lyra.factory import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def client_no_cache():
    cache.use_cache(False)
    print("cache disabled")
    app = create_app()
    with TestClient(app) as client:
        yield client
    cache.use_cache(True)
    print("cache re-enabled")


@pytest.fixture
def client_no_cache_foreground():
    cache.use_cache(False)
    print("cache disabled")
    app = create_app(settings_override={"FORCE_FOREGROUND": True})
    with TestClient(app) as client:
        yield client
    cache.use_cache(True)
    print("cache re-enabled")


def _get_admin_routes():
    app = create_app()
    paths = []
    for route in app.routes:
        if "admin" in getattr(route, "tags", []):
            paths.append(route.path)
    return paths


@pytest.fixture(params=_get_admin_routes())
def admin_route(request):
    yield request.param
