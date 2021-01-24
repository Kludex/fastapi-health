import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from fastapi_health import health


def healthy():
    return True


def healthy_with_dependency(condition_banana: bool = Depends(healthy)):
    return condition_banana


async def async_health():
    return True


def sick():
    return False


@pytest.mark.parametrize(
    "conditions,status_code",
    [
        ([healthy], 200),
        ([healthy_with_dependency], 200),
        ([async_health], 200),
        ([sick], 503),
        ([async_health, healthy], 200),
        ([healthy, sick], 503),
    ],
)
def test_health(conditions, status_code):
    app = FastAPI()
    app.add_api_route("/health", health(conditions))
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == status_code
