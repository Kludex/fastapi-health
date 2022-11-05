from collections import namedtuple
from dataclasses import dataclass, field
from enum import Enum
from inspect import Parameter, Signature
from typing import Any, Callable, Dict, List, Optional, cast

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field


# https://inadarei.github.io/rfc-healthcheck/#name-the-checks-object-2
class Check(BaseModel):
    componentId: Optional[str] = Field(
        None,
        description="Unique identifier of an instance of a specific sub-component/dependency of a service.",
    )
    componentType: Optional[str] = Field(
        None, description="Type of the sub-component/dependency of a service."
    )
    observedValue: Any = Field(None, description="The observed value of the component.")
    observedUnit: Optional[str] = Field(None, description="The unit of the observed value.")
    status: Optional[str] = Field(
        None, description="Raw error output, in case of 'fail' or 'warn' states."
    )
    affectedEndpoints: Optional[List[str]] = Field(None, description="List of affected endpoints.")
    time: str  # datetime
    output: str
    links: Dict[str, str]


class ServiceStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


# https://inadarei.github.io/rfc-healthcheck/#name-api-health-response-2
class HealthBody(BaseModel):
    status: ServiceStatus = Field(..., description="Indicates the service status.")
    version: Optional[str] = Field(None, description="The version of the service.")
    releaseId: Optional[str] = Field(None, description="The release ID of the service.")
    notes: Optional[List[str]] = Field(None, description="Notes relevant to the current status.")
    # output: Dict[str, Any]
    # checks: Optional[List[Check]] = Field(
    #     None,
    #     description=(
    #         "Provides detailed health statuses of additional downstream systems"
    #         " and endpoints which can affect the overall health of the main API."
    #     ),
    # )
    links: Optional[Dict[str, str]] = Field(None, description="Links to related resources.")
    serviceId: Optional[str] = Field(None, description="The ID of the service.")
    description: Optional[str] = Field(None, description="The description of the service.")


@dataclass
class Condition:
    name: str
    callable: Callable[..., Check]


Status = namedtuple("Status", ["code", "name"])


@dataclass
class HealthEndpoint:
    conditions: List[Condition] = field(default_factory=list)
    allow_version: bool = field(default=False)
    version: Optional[str] = field(default=None)

    allow_description: bool = field(default=False)
    description: Optional[str] = field(default=None)

    release_id: Callable[..., Optional[None]] = field(default=lambda: None)
    service_id: Optional[str] = field(default=None)

    pass_status: Status = field(default=Status(code=200, name="pass"))
    fail_status: Status = field(default=Status(code=503, name="fail"))
    warn_status: Status = field(default=Status(code=200, name="warn"))

    allow_output: bool = field(default=True)

    links: Optional[Dict[str, str]] = field(default=None)
    notes: Callable[..., Optional[List[str]]] = field(default=lambda: None)

    def __post_init__(self):
        HealthEndpoint.__call__ = self.prepare_call()

    def prepare_call(self):
        if not self.allow_version and self.version:
            raise ValueError(f"Version is not allowed, but version '{self.version}' was provided.")
        if not self.allow_description and self.description:
            raise ValueError("Description is not allowed, but it was provided.")

        def endpoint(
            self: "HealthEndpoint",
            request: Request,
            release_id: Optional[str] = Depends(self.release_id),
            notes: Optional[List[str]] = Depends(self.notes),
            conditions: Dict[str, Check] = Depends(self._aggregate_conditions()),
        ) -> JSONResponse:
            app = cast(FastAPI, request.app)
            status = self._get_service_status(conditions)

            version: Optional[str] = None
            if self.allow_version:
                version = self.version or app.version

            description: Optional[str] = None
            if self.allow_description:
                description = self.description or app.description

            body = HealthBody(
                status=status.name,
                version=version,
                description=description,
                releaseId=release_id,
                serviceId=self.service_id,
                notes=notes,
                links=self.links,
            )
            return JSONResponse(
                content=body.dict(exclude_none=True),
                status_code=status.code,
                media_type="application/health+json",
            )

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
            if check.status == self.fail_status.name:
                return self.fail_status
            if check.status == self.warn_status.name:
                warns += 1
        if checks and warns == len(checks):
            return self.warn_status
        return self.pass_status


if __name__ == "__main__":

    def check_redis() -> Check:
        return Check(status="pass")

    def check_postgres() -> Check:
        return Check(status="fail")

    app = FastAPI(
        routes=[
            APIRoute(
                "/health",
                HealthEndpoint(
                    conditions=[
                        Condition("postgres:connection", check_postgres),
                        Condition("redis:connection", check_redis),
                    ]
                ),
            )
        ]
    )
