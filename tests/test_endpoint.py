from typing import Callable

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from fastapi_health import HealthEndpoint


@pytest.fixture(scope="session")
def client_factory() -> Callable[..., TestClient]:
    def factory(**kwargs) -> TestClient:
        app = FastAPI(routes=[APIRoute(path="/health", endpoint=HealthEndpoint(**kwargs))])
        return TestClient(app)

    return factory


def test_allow_version(client_factory: Callable[..., TestClient]) -> None:
    res = client_factory(allow_version=True).get("/health")
    assert res.status_code == 200
    assert res.json() == {"version": "0.1.0", "status": "pass"}


def test_allow_version_define_version(client_factory: Callable[..., TestClient]) -> None:
    res = client_factory(allow_version=True, version="1.0.0").get("/health")
    assert res.status_code == 200
    assert res.json() == {"version": "1.0.0", "status": "pass"}


def test_not_allowed_version(client_factory: Callable[..., TestClient]) -> None:
    with pytest.raises(ValueError) as exc_info:
        client_factory(allow_version=False, version="1.0.0")
    assert exc_info.value.args[0] == "Version is not allowed, but version '1.0.0' was provided."


def test_release_id(client_factory: Callable[..., TestClient]) -> None:
    res = client_factory(release_id=lambda: "123").get("/health")
    assert res.status_code == 200
    assert res.json() == {"releaseId": "123", "status": "pass"}


def test_service_id(client_factory: Callable[..., TestClient]) -> None:
    res = client_factory(service_id="123").get("/health")
    assert res.status_code == 200
    assert res.json() == {"serviceId": "123", "status": "pass"}
