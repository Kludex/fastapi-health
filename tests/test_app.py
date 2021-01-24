from fastapi import FastAPI

from fastapi_health import HealthRoute


def potato():
    return True


def banana():
    return True


health_route = HealthRoute([potato, banana])

app = FastAPI()
app.add_api_route("/potato", health_route)
