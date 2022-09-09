import pytests
from paatr.factory import create_app
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def test_client():
    yield TestClient(create_app())
