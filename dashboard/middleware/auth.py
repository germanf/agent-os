import hmac
import json
import os
import typing

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

AUTH_EXEMPT_PATHS = {"/api/health"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: typing.Callable) -> Response:
        if request.url.path in AUTH_EXEMPT_PATHS:
            return await call_next(request)
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            return Response(status_code=401, headers={"WWW-Authenticate": "Basic"})
        try:
            encoded = auth_header[len("Basic "):]
            decoded = __import__("base64").b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)
        except Exception:
            return Response(status_code=401, headers={"WWW-Authenticate": "Basic"})
        env_user = os.environ.get("DASH_USER", "")
        env_pass = os.environ.get("DASH_PASS", "")
        if not env_user or not env_pass:
            try:
                creds_path = os.path.join(os.path.dirname(__file__), "..", ".credentials.json")
                if os.path.exists(creds_path):
                    with open(creds_path) as f:
                        creds = json.load(f)
                    env_user = creds.get("user", "")
                    env_pass = creds.get("pass", "")
            except Exception:
                pass
        if not env_user or not env_pass:
            return Response(status_code=500, content="Server configuration error")
        expected = f"{env_user}:{env_pass}"
        if len(expected) != len(decoded):
            return Response(status_code=401, headers={"WWW-Authenticate": "Basic"})
        if not hmac.compare_digest(decoded, expected):
            return Response(status_code=401, headers={"WWW-Authenticate": "Basic"})
        return await call_next(request)
