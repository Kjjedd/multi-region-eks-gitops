from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.logging_config import request_id_var

log = structlog.get_logger("http")

REQUEST_ID_HEADER = "X-Request-ID"
PROCESS_TIME_HEADER = "X-Process-Time"


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        rid = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        token = request_id_var.set(rid)
        start = time.perf_counter()
        try:
            structlog.contextvars.bind_contextvars(request_id=rid)
            response = await call_next(request)
        except Exception:
            elapsed = time.perf_counter() - start
            log.exception(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_s=round(elapsed, 4),
            )
            raise
        else:
            elapsed = time.perf_counter() - start
            response.headers[REQUEST_ID_HEADER] = rid
            response.headers[PROCESS_TIME_HEADER] = f"{elapsed:.4f}"
            log.info(
                "request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_s=round(elapsed, 4),
            )
            return response
        finally:
            structlog.contextvars.unbind_contextvars("request_id")
            request_id_var.reset(token)


class ServedByMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, region: str, env: str, hostname: str) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.region = region
        self.env = env
        self.hostname = hostname

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Served-Region"] = self.region
        response.headers["X-Served-Env"] = self.env
        response.headers["X-Served-Pod"] = self.hostname
        return response
