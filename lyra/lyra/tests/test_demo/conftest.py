import pytest
from fastapi.testclient import TestClient

from lyra.factory import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as client:
        yield client
