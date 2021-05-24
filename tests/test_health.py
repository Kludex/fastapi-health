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


def test_multiple_condition():
    def healthy():
        return True

    def also_healthy():
        return True

    app = FastAPI()
    app.add_api_route("/health", health([healthy, also_healthy]))
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200


def test_sick_condition():
    def sick():
        return False

    def healthy():
        return True

    app = FastAPI()
    app.add_api_route("/health", health([sick, healthy]))
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


def test_hybrid():
    def healthy_dict():
        return True

    def sick():
        return False

    def also_healthy_dict():
        return {"banana": "yes"}

    app = FastAPI()
    app.add_api_route("/health", health([healthy_dict, also_healthy_dict, sick]))
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 503
        assert res.json() == {"banana": "yes"}


def test_success_handler():
    async def success_handler(**kwargs):
        return kwargs

    def healthy():
        return True

    def another_healthy():
        return True

    app = FastAPI()
    app.add_api_route(
        "/health", health([healthy, another_healthy], success_handler=success_handler)
    )
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"healthy": True, "another_healthy": True}


def test_custom_output():
    async def success_handler(**kwargs):
        is_success = all(kwargs.values())
        return {
            "status": "success" if is_success else "failure",
            "results": [
                {"condition": condition, "output": value}
                for condition, value in kwargs.items()
            ],
        }

    def sick():
        return False

    def healthy():
        return True

    app = FastAPI()
    app.add_api_route(
        "/health", health([sick, healthy], failure_handler=success_handler)
    )
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 503
        assert res.json() == {
            "status": "failure",
            "results": [
                {"condition": "sick", "output": False},
                {"condition": "healthy", "output": True},
            ],
        }
