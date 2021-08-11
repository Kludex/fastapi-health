import importlib.metadata as importlib_metadata

from fastapi_health.route import health

__version__ = importlib_metadata.version(__name__)
__all__ = ["health"]
