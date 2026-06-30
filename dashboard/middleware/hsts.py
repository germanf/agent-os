import typing

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class HSTSHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next: typing.Callable) -> Response:
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
