<h1 align="center">
    <strong>FastAPI Health 🚑️</strong>
</h1>
<p align="center">
    <a href="https://github.com/Kludex/fastapi-health" target="_blank">
        <img src="https://img.shields.io/github/last-commit/Kludex/fastapi-health" alt="Latest Commit">
    </a>
        <img src="https://img.shields.io/github/workflow/status/Kludex/fastapi-health/Test">
        <img src="https://img.shields.io/codecov/c/github/Kludex/fastapi-health">
    <br />
    <a href="https://pypi.org/project/fastapi-health" target="_blank">
        <img src="https://img.shields.io/pypi/v/fastapi-health" alt="Package version">
    </a>
    <img src="https://img.shields.io/pypi/pyversions/fastapi-health">
    <img src="https://img.shields.io/github/license/Kludex/fastapi-health">
</p>

The goal of this package is to help you to implement the [Health Check API](https://microservices.io/patterns/observability/health-check-api.html) pattern.

## Installation

``` bash
pip install fastapi-health
```

## Quick Start

Create the health check endpoint dynamically using different conditions. Each condition is a
callable, and you can even have dependencies inside of it:

```python
from fastapi import FastAPI, Depends
from fastapi_health import health


def get_session():
    return True


def is_database_online(session: bool = Depends(get_session)):
    return session


app = FastAPI()
app.add_api_route("/health", health([is_database_online]))
```

## Advanced Usage

The `health()` method receives the following parameters:
- `conditions`: A list of callables that represents the conditions of your API, it can return either `bool` or a `dict`.
- `success_handler`: An optional callable which receives the `conditions` results and returns a dictionary that will be the content response of a successful health call.
- `failure_handler`: An optional callable analogous to `success_handler` for failure scenarios.
- `success_status`: An integer that overwrites the default status (200) in case of success.
- `failure_status`: An integer that overwrites the default status (503) in case of failure.

It's important to notice that you can have a _peculiar_ behavior in case of hybrid return statements (`bool` and `dict`) on the conditions.
For example:

``` Python
from fastapi import FastAPI
from fastapi_health import health


def pass_condition():
    return {"database": "online"}


def sick_condition():
    return False


app = FastAPI()
app.add_api_route("/health", health([pass_condition, sick_condition]))
```

This will generate a response composed by the status being 503 (default `failure_status`), because `sick_condition` returns `False`, and the JSON body `{"database": "online"}`. It's not wrong, or a bug. It's meant to be like this.

## License

This project is licensed under the terms of the MIT license.
