# FastAPI Health :ambulance:

The goal of this package is to help you to implement the
[**Health Check API**] pattern.

## Installation

```bash
pip install fastapi-health
```

## Usage

The easier way to use this package is to use the **`health`** function.

Create the health check endpoint dynamically using different conditions.
Each condition is a callable, and you can even have dependencies inside of it:

=== "PostgreSQL"

    ```python
    import asyncio

    from fastapi import FastAPI, Depends
    from fastapi_health import health
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.ext.asyncio import AsyncSession

    # You need to implement yourself 👇
    from app.database import get_session


    async def is_database_online(session: AsyncSession = Depends(get_session)):
        try:
            await asyncio.wait_for(session.execute("SELECT 1"), timeout=30)
        except (SQLAlchemyError, TimeoutError):
            return False
        return True


    app = FastAPI()
    app.add_api_route("/health", health([is_database_online]))
    ```

=== "Redis"

    ```python
    import asyncio

    from fastapi import FastAPI, Depends
    from fastapi_health import health
    from redis import ConnectionError
    from redis.asyncio import Redis

    # You need to implement yourself 👇
    from app.redis import get_redis


    async def is_redis_alive(client: Redis = Depends(get_redis)):
        try:
            await asyncio.wait_for(client.check_health(), timeout=30)
        except (ConnectionError, RuntimeError, TimeoutError):
            return False
        return True


    app = FastAPI()
    app.add_api_route("/health", health([is_redis_alive]))
    ```

=== "MongoDB"

    ```python
    import asyncio

    from fastapi import FastAPI, Depends
    from fastapi_health import health
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo.errors import ServerSelectionTimeoutError

    # You need to implement yourself 👇
    from app.mongodb import get_mongo


    async def is_mongo_alive(client: AsyncIOMotorClient = Depends(get_mongo)):
        try:
            await asyncio.wait_for(client.server_info(), timeout=30)
        except (ServerSelectionTimeoutError, TimeoutError):
            return False
        return True


    app = FastAPI()
    app.add_api_route("/health", health([is_mongo_alive]))
    ```

You can check the [**API reference**] for more details.

[**Health Check API**]: https://microservices.io/patterns/observability/health-check-api.html
[**API Reference**]: api/#fastapi_health.route.health

