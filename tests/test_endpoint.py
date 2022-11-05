from typing import Any
from datetime import datetime
from fastapi_health.endpoint import Condition, Check, Status

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute

from fastapi_health import HealthEndpoint
import httpx


def healthy() -> Check:
    return Check()


def healthy_with_time() -> Check:
    return Check(time=datetime(year=2022, month=1, day=1).isoformat())


async def healthy_async() -> Check:
    return Check()


def warn() -> Check:
    return Check(status="warn")


def fail() -> Check:
    return Check(status="fail")


def release_id() -> str:
    return "release_id"


pass_condition = Condition(name="postgres:connection", calls=[healthy, healthy_async])
fail_condition = Condition(name="postgres:connection", calls=[fail])
warn_condition = Condition(name="postgres:connection", calls=[warn])
pass_with_time = Condition(name="postgres:connection", calls=[healthy_with_time])


def create_app(*args: Any, **kwargs: Any) -> FastAPI:
    app = FastAPI(routes=[APIRoute("/health", HealthEndpoint(*args, **kwargs))])
    app.description = "Test app"
    return app


healthy_app = create_app(conditions=[pass_condition])
use_version_app = create_app(conditions=[pass_condition], allow_version=True)
use_custom_version_app = create_app(conditions=[pass_condition], version="1.0.0")
release_id_app = create_app(conditions=[pass_condition], release_id=release_id)
service_id_app = create_app(conditions=[pass_condition], service_id="service_id")
pass_status_app = create_app(conditions=[pass_condition], pass_status=Status(200, "ok"))
fail_app = create_app(conditions=[fail_condition])
warn_app = create_app(conditions=[warn_condition])
allow_description_app = create_app(conditions=[pass_condition], allow_description=True)
description_app = create_app(conditions=[pass_condition], description="Test")
time_app = create_app(conditions=[pass_with_time])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "app, status, body",
    [
        (healthy_app, 200, {"status": "pass"}),
        (use_version_app, 200, {"status": "pass", "version": "0.1.0"}),
        (use_custom_version_app, 200, {"status": "pass", "version": "1.0.0"}),
        (release_id_app, 200, {"status": "pass", "releaseId": "release_id"}),
        (service_id_app, 200, {"status": "pass", "serviceId": "service_id"}),
        (pass_status_app, 200, {"status": "ok"}),
        (
            fail_app,
            503,
            {"status": "fail", "checks": {"postgres:connection": [{"status": "fail"}]}},
        ),
        (
            warn_app,
            200,
            {"status": "warn", "checks": {"postgres:connection": [{"status": "warn"}]}},
        ),
        (allow_description_app, 200, {"status": "pass", "description": "Test app"}),
        (description_app, 200, {"status": "pass", "description": "Test"}),
        (
            time_app,
            200,
            {
                "status": "pass",
                "checks": {"postgres:connection": [{"time": "2022-01-01T00:00:00"}]},
            },
        ),
    ],
)
async def test_health_endpoint(app, status: int, body: dict) -> None:
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == status
        assert response.json() == body
