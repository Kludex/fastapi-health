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

## Usage

Using this package, you can create the health check endpoint dynamically using different conditions. Each condition is a
callable and you can even have dependencies inside of it.

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

The `/health` endpoint on the example can return two possible response status code:
- 200 (Ok): conditions are satisfied.
- 503 (Service Unavailable): at least one condition is false.

## License

This project is licensed under the terms of the MIT license.
