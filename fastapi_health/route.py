from inspect import Parameter, Signature
from typing import Callable, List

from fastapi import Depends, Response


def health(conditions: List[Callable]):
    def endpoint(**dependencies):
        if all([dependency for dependency in dependencies.values()]):
            return Response(status_code=200)
        return Response(status_code=503)

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
