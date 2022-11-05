from typing import Any

import pytest
from fastapi import Depends, FastAPI
from fastapi.routing import APIRoute
from httpx import AsyncClient

from fastapi_health import health


def healthy():
    return True


def another_healthy():
    return True


def sick():
    return False


def with_dependency(condition_banana: bool = Depends(healthy)):
    return condition_banana


async def healthy_async():
    return True


def healthy_dict():
    return {"potato": "yes"}


def another_health_dict():
    return {"banana": "yes"}


def create_app(*args: Any, **kwargs: Any) -> FastAPI:
    return FastAPI(routes=[APIRoute("/health", health(*args, **kwargs))])


async def success_handler(**kwargs):
    return kwargs


async def custom_failure_handler(**kwargs):
    is_success = all(kwargs.values())
    return {
        "status": "success" if is_success else "failure",
        "results": [
            {"condition": condition, "output": value}
            for condition, value in kwargs.items()
        ],
    }


healthy_app = create_app([healthy])
multiple_healthy_app = create_app([healthy, another_healthy])
sick_app = create_app([healthy, sick])
with_dependency_app = create_app([with_dependency])
healthy_async_app = create_app([healthy_async])
healthy_dict_app = create_app([healthy_dict])
multiple_healthy_dict_app = create_app([healthy_dict, another_health_dict])
hybrid_app = create_app([healthy, sick, healthy_dict])
success_handler_app = create_app([healthy], success_handler=success_handler)
failure_handler_app = create_app(
    [sick, healthy], failure_handler=custom_failure_handler
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "app, status_code, body",
    (
        (healthy_app, 200, {}),
        (multiple_healthy_app, 200, {}),
        (sick_app, 503, {}),
        (with_dependency_app, 200, {}),
        (healthy_async_app, 200, {}),
        (healthy_dict_app, 200, {"potato": "yes"}),
        (multiple_healthy_dict_app, 200, {"potato": "yes", "banana": "yes"}),
        (hybrid_app, 503, {"potato": "yes"}),
        (success_handler_app, 200, {"healthy": True}),
        (
            failure_handler_app,
            503,
            {
                "status": "failure",
                "results": [
                    {"condition": "sick", "output": False},
                    {"condition": "healthy", "output": True},
                ],
            },
        ),
    ),
)
async def test_health(app: FastAPI, status_code: int, body: dict) -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == status_code
        assert res.json() == body
