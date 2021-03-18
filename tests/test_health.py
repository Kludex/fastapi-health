from typing import Any, Callable, Dict

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from fastapi_health import health


def test_single_condition():
    def healthy():
        return True

    app = FastAPI()
    app.add_api_route("/health", health([healthy]))
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200


def test_sick_condition():
    def sick():
        return False

    app = FastAPI()
    app.add_api_route("/health", health([sick]))
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 503


def test_endpoint_with_dependency():
    def healthy():
        return True

    def healthy_with_dependency(condition_banana: bool = Depends(healthy)):
        return condition_banana

    app = FastAPI()
    app.add_api_route("/health", health([healthy_with_dependency]))
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200


def test_coroutine_condition():
    async def async_health():
        return True

    app = FastAPI()
    app.add_api_route("/health", health([async_health]))
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200


def test_json_response():
    def healthy_dict():
        return {"potato": "yes"}

    app = FastAPI()
    app.add_api_route("/health", health([healthy_dict]))
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"potato": "yes"}


def test_concatenate_response():
    def healthy_dict():
        return {"potato": "yes"}

    def also_healthy_dict():
        return {"banana": "yes"}

    app = FastAPI()
    app.add_api_route("/health", health([healthy_dict, also_healthy_dict]))
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"potato": "yes", "banana": "yes"}
