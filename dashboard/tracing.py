from __future__ import annotations

from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

_current_request_id: ContextVar[str] = ContextVar("request_id", default="")


def request_id() -> str:
    return _current_request_id.get()


_request_id: ContextVar[str] = ContextVar("request_id", default="")
_tracer = None


def _setup():
    global _tracer
    try:
        from headroom import configure_otel_metrics, get_headroom_tracer
        from headroom.observability import OTelMetricsConfig

        cfg = OTelMetricsConfig(enabled=True, exporter="console")
        configure_otel_metrics(cfg)
        _tracer = get_headroom_tracer()
        logger.info("OpenTelemetry tracing enabled (console exporter)")
    except Exception as exc:
        logger.warning("Failed to configure OTel: {}", exc)


_setup()


class TracingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = request.headers.get("X-Request-ID", uuid4().hex[:12])
        _request_id.set(rid)

        span = _tracer.start_span(f"{request.method} {request.url.path}") if _tracer else None
        if span:
            span.set_attribute("request_id", rid)
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))

        try:
            response = await call_next(request)
            if span:
                span.set_attribute("http.status_code", response.status_code)
            return response
        finally:
            if span:
                span.end()
