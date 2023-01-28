from inspect import Parameter, Signature
from typing import TypeVar
from typing import Any, Awaitable, Callable, Coroutine, Dict, List, Union

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


T = TypeVar("T")


async def default_handler(**kwargs: T) -> Dict[str, T]:
    """Default handler for health check route.

    It's used by the success and failure handlers.

    Returns:
        Dict[str, T]: A dictionary with the results of the conditions.
    """
    output = {}
    for value in kwargs.values():
        if isinstance(value, dict):
            output.update(value)
    return output


def health(
    conditions: List[Callable[..., Union[Dict[str, Any], bool]]],
    *,
    success_handler: Callable[..., Awaitable[dict]] = default_handler,
    failure_handler: Callable[..., Awaitable[dict]] = default_handler,
    success_status: int = 200,
    failure_status: int = 503,
) -> Callable[..., Coroutine[None, None, JSONResponse]]:
    """Create a health check route.

    Args:
        conditions (List[Callable[..., Dict[str, Any] | bool]]): A list of callables
            that represents the condition of your service.
        success_handler (Callable[..., Awaitable[dict]]): A callable which receives
            the `conditions` results, and returns a dictionary that will be the content
            response of a successful health call.
        failure_handler (Callable[..., Awaitable[dict]]): A callable analogous to
            `success_handler` for failure scenarios.
        success_status (int): An integer that overwrites the default status (`200`) in
            case of success.
        failure_status (int): An integer that overwrites the default status (`503`) in
            case of failure.

    Returns:
        Callable[..., Awaitable[JSONResponse]]: The health check route.
    """

    async def endpoint(**dependencies) -> JSONResponse:
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
