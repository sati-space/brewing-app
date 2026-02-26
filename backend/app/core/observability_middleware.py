from __future__ import annotations

import json
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.services.observability import observability_tracker

logger = logging.getLogger("brewpilot.request")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id

        started = perf_counter()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            duration_ms = (perf_counter() - started) * 1000
            status_code = 500

            observability_tracker.record(
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
            )

            payload = {
                "event": "request_error",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "user_id": getattr(request.state, "user_id", None),
            }
            logger.exception(json.dumps(payload))

            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id},
            )
        else:
            duration_ms = (perf_counter() - started) * 1000

            observability_tracker.record(
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
            )

            payload = {
                "event": "request_completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "user_id": getattr(request.state, "user_id", None),
            }

            if status_code >= 500:
                logger.error(json.dumps(payload))
            elif status_code >= 400:
                logger.warning(json.dumps(payload))
            else:
                logger.info(json.dumps(payload))

        response.headers["X-Request-ID"] = request_id
        return response
