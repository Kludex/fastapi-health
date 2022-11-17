from dataclasses import dataclass, field
from collections import defaultdict
from starlette._utils import is_async_callable
from anyio import to_thread
import anyio
from datetime import datetime
from typing import Any, Callable, Dict, List, DefaultDict, Optional, cast, Union, Awaitable

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator


# https://inadarei.github.io/rfc-healthcheck/#name-the-checks-object-2
class Check(BaseModel):
    componentId: Optional[str] = Field(
        default=None,
        description="Unique identifier of an instance of a specific sub-component/dependency of a service.",
    )
    componentType: Optional[str] = Field(
        default=None, description="Type of the sub-component/dependency of a service."
    )
    observedValue: Any = Field(default=None, description="The observed value of the component.")
    observedUnit: Optional[str] = Field(default=None, description="The unit of the observed value.")
    status: Optional[str] = Field(default=None, description="Indicates the service status.")
    affectedEndpoints: Optional[List[str]] = Field(
        default=None, description="List of affected endpoints."
    )
    time: Optional[str] = Field(
        default=None, description="Datetime at which the 'observedValue' was recorded."
    )
    output: Optional[str] = Field(
        default=None,
        description=(
            'Raw error output, in case of "fail" or "warn" states. '
            'This field SHOULD be omitted for "pass" state.'
        ),
    )
    links: Optional[Dict[str, str]] = Field(default=None)  # TODO: missing description

    @validator("time")
    def validate_iso_8061(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v)
        except ValueError as exc:  # pragma: no cover
            raise exc
        return v


class HealthBody(BaseModel):
    status: str = Field(default=..., description="Indicates the service status.")
    version: Optional[str] = Field(default=None, description="The version of the service.")
    releaseId: Optional[str] = Field(default=None, description="The release ID of the service.")
    notes: Optional[List[str]] = Field(
        default=None, description="Notes relevant to the current status."
    )
    output: Optional[str] = Field(
        default=None,
        description=(
            'Raw error output, in case of "fail" or "warn" states. '
            'This field SHOULD be omitted for "pass" state.'
        ),
    )
    checks: Optional[Dict[str, List[Check]]] = Field(
        default=None,
        description=(
            "Provides detailed health statuses of additional downstream systems"
            " and endpoints which can affect the overall health of the main API."
        ),
    )
    links: Optional[Dict[str, str]] = Field(default=None, description="Links to related resources.")
    serviceId: Optional[str] = Field(default=None, description="The ID of the service.")
    description: Optional[str] = Field(default=None, description="The description of the service.")


class Condition(BaseModel):
    name: str = Field(default=..., description="The name of the condition. Must be unique.")
    calls: List[Callable[[], Union[Check, Awaitable[Check]]]] = Field(
        default=..., description="The function to call to check the condition."
    )


@dataclass(frozen=True)
class Status:
    code: int
    name: str


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
        def endpoint(
            self: "HealthEndpoint",
            request: Request,
            release_id: Optional[str] = Depends(self.release_id),
            notes: Optional[List[str]] = Depends(self.notes),
            checks: Dict[str, List[Check]] = Depends(self.run_conditions),
        ) -> JSONResponse:
            app = cast(FastAPI, request.app)
            status = self._get_service_status(checks)

            if self.version:
                version = self.version
            elif self.allow_version:
                version = app.version
            else:
                version = None

            if self.description:
                description = self.description
            elif self.allow_description:
                description = app.description
            else:
                description = None

            body = HealthBody(
                status=status.name,
                version=version,
                description=description,
                releaseId=release_id,
                serviceId=self.service_id,
                notes=notes,
                links=self.links,
                output=None,  # TODO: add output
                checks=checks or None,
            )
            return JSONResponse(
                content=body.dict(exclude_none=True),
                status_code=status.code,
                media_type="application/health+json",
            )

        return endpoint

    async def run_conditions(self) -> Dict[str, List[Check]]:
        results: DefaultDict[str, List[Check]] = defaultdict(list)

        async def _run_condition(
            name: str, call: Callable[[], Union[Check, Awaitable[Check]]]
        ) -> None:
            if is_async_callable(call):
                result = await call()
            else:
                result = await to_thread.run_sync(call)
            result = cast(Check, result)
            if result.dict(exclude_none=True):
                results[name].append(result)

        async with anyio.create_task_group() as tg:
            for condition in self.conditions:
                for call in condition.calls:
                    tg.start_soon(_run_condition, condition.name, call)

        return results

    def _get_service_status(self, checks: Dict[str, List[Check]]) -> Status:
        total_checks = 0
        warns = 0
        for checklist in checks.values():
            for check in checklist:
                total_checks += 1
                if check.status == self.fail_status.name:
                    return self.fail_status
                if check.status == self.warn_status.name:
                    warns += 1
        if checks and warns == total_checks:
            return self.warn_status
        return self.pass_status
