from collections import namedtuple
from dataclasses import dataclass, field
from inspect import Parameter, Signature, signature
from typing import Any, Callable, Dict, List, Optional, TypedDict, cast

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse


class DictNoNone(dict):
    def __setitem__(self, key, value):
        if key in self or value is not None:
            dict.__setitem__(self, key, value)


# https://datatracker.ietf.org/doc/html/draft-inadarei-api-health-check-06#section-4
class Check(TypedDict, total=False):
    componentId: str
    componentType: str
    observedValue: Any
    observedUnit: str
    status: str
    affectedEndpoints: List[str]
    time: str  # datetime
    output: str
    links: Dict[str, str]


# https://datatracker.ietf.org/doc/html/draft-inadarei-api-health-check-06#section-3
class HealthBody(TypedDict, total=False):
    status: str
    version: str
    releaseId: str
    notes: List[str]
    output: Dict[str, Any]
    checks: List[Check]
    links: Dict[str, str]
    serviceId: str
    description: str


@dataclass
class Condition:
    name: str
    callable: Callable[..., Check]


Status = namedtuple("Status", ["code", "name"])


@dataclass
class HealthRoute:
    conditions: List[Condition] = field(default_factory=list)
    allow_version: bool = field(default=False)
    version: Optional[str] = field(default=None)

    allow_description: bool = field(default=False)
    description: Optional[str] = field(default=None)

    release_id: Optional[Callable[..., str]] = field(default=lambda: None)
    service_id: Optional[str] = field(default=None)

    pass_status: Status = field(default=Status(code=200, name="pass"))
    fail_status: Status = field(default=Status(code=503, name="fail"))
    warn_status: Status = field(default=Status(code=200, name="warn"))

    allow_output: bool = field(default=True)

    links: Optional[Dict[str, str]] = field(default=None)
    notes: Callable[..., Optional[List[str]]] = field(default=lambda: None)

    def __post_init__(self):
        HealthRoute.__call__ = HealthRoute.prepare_call(self)

    def prepare_call(self):
        if not self.allow_version and self.version:
            raise ValueError(
                f"Version is not allowed, but version '{self.version}' was provided."
            )
        if not self.allow_description and self.description:
            raise ValueError("Description is not allowed, but it was provided.")

        def endpoint(self: "HealthRoute", request: Request, **kwargs: Any) -> None:
            body: HealthBody = DictNoNone()
            app = cast(FastAPI, request.app)
            status = self._get_service_status(kwargs.get("conditions"))

            if self.allow_version:
                body["version"] = self.version or app.version
            if self.allow_description:
                body["description"] = self.description or app.description
            body["serviceId"] = self.service_id
            body["releaseId"] = kwargs.get("release_id")
            body["status"] = status.name
            body["links"] = self.links
            body["notes"] = kwargs.get("notes")
            return JSONResponse(
                content=body,
                status_code=status.code,
                media_type="application/health+json",
            )

        sig = signature(endpoint)
        sig = sig.replace(parameters=tuple(sig.parameters.values())[:-1])
        params = [
            Parameter(
                name="release_id",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=Depends(self.release_id),
            ),
            Parameter(
                name="conditions",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=Depends(self._aggregate_conditions()),
            ),
            Parameter(
                name="notes",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=Depends(self.notes),
            ),
        ]
        endpoint.__signature__ = Signature(list(sig.parameters.values()) + params)
        return endpoint

    def _aggregate_conditions(self) -> Callable[..., dict]:
        def dependency(**kwargs: Any) -> dict:
            return kwargs

        parameters = [
            Parameter(
                name=condition.callable.__name__,
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=Depends(condition.callable),
            )
            for condition in self.conditions
        ]
        dependency.__signature__ = Signature(parameters)
        return dependency

    def _get_service_status(self, checks: Dict[str, Check]) -> Status:
        warns = 0
        for check in checks.values():
            if check["status"] == self.fail_status.name:
                return self.fail_status
            if check["status"] == self.warn_status.name:
                warns += 1
        if checks and warns == len(checks):
            return self.warn_status
        return self.pass_status


def check_redis() -> Check:
    return Check(status="pass")


def check_postgres() -> Check:
    return Check(status="fail")


app = FastAPI()
app.add_api_route(
    "/health",
    HealthRoute(
        conditions=[
            Condition("postgres:connection", check_postgres),
            Condition("redis:connection", check_redis),
        ]
    ),
)
