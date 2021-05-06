from collections import ChainMap
from inspect import Parameter, Signature
from typing import Any, Callable, Dict, List, Optional, Union

from fastapi import Depends
from fastapi.responses import JSONResponse


def health(
    conditions: List[Callable[..., Union[Dict[str, Any], bool]]],
    *,
    success_output: Optional[Dict[str, Any]] = None,
    failure_output: Optional[Dict[str, Any]] = None,
    success_status: int = 200,
    failure_status: int = 503,
):
    async def endpoint(**dependencies):
        values = [dependency for dependency in dependencies.values()]
        output = dict(ChainMap(*filter(lambda x: isinstance(x, dict), values)))
        if all(values):
            return JSONResponse(success_output or output, status_code=success_status)
        return JSONResponse(failure_output or output, status_code=failure_status)

    params = []
    for condition in conditions:
        params.append(
            Parameter(
                f"param_{condition.__name__}",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                annotation=bool,
                default=Depends(condition),
            )
        )
    endpoint.__signature__ = Signature(params)
    return endpoint
