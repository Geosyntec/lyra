import pytest

from lyra.core import cache, security


def mockflush():
    print("mocked flush")
    pass


def mockuse_cache(state):
    print("mocked use cache")
    pass


@pytest.fixture
def mock_cache(monkeypatch):
    monkeypatch.setattr(cache, "flush", mockflush)
    monkeypatch.setattr(cache, "use_cache", mockuse_cache)


def test_auth_routes(client, admin_route):
    """ensure that any route with an "auth" tag is not accessible."""
    response = client.get(admin_route)
    assert response.status_code == 401, admin_route  # not authorized


@pytest.mark.integration
def test_auth_routes_as_admin(client, mock_cache, admin_route):
    """ensure that any route with an "auth" tag is not accessible."""
    client.app.dependency_overrides[security.is_admin] = lambda: True
    response = client.get(admin_route)
    client.app.dependency_overrides.pop(security.is_admin)

    assert response.status_code == 200, admin_route
