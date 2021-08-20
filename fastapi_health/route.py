from inspect import Parameter, Signature
from typing import Any, Awaitable, Callable, Dict, List, Union

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


async def default_handler(**kwargs) -> Dict[str, Any]:
    output = {}
    for value in kwargs.values():
        if isinstance(value, dict):
            output.update(value)
    return output


def health(
    conditions: List[Callable[..., Union[Dict[str, Any], bool]]],
    *,
    success_handler: Callable[..., Awaitable] = default_handler,
    failure_handler: Callable[..., Awaitable] = default_handler,
    success_status: int = 200,
    failure_status: int = 503,
):
    async def endpoint(**dependencies):
        if all(dependencies.values()):
            handler = success_handler
            status_code = success_status
        else:
            handler = failure_handler
            status_code = failure_status

        output = await handler(**dependencies)
        return JSONResponse(jsonable_encoder(output), status_code=status_code)

    params = []
    for condition in conditions:
        params.append(
            Parameter(
                f"{condition.__name__}",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                annotation=bool,
                default=Depends(condition),
            )
        )
    endpoint.__signature__ = Signature(params)
    return endpoint
