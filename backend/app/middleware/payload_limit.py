"""Request Payload Size Limiter Middleware.
Protects against Denial of Service (DoS) and memory exhaustion from oversized request bodies.
"""

import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Default limit: 2 Megabytes
DEFAULT_MAX_PAYLOAD_BYTES = 2 * 1024 * 1024


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    """Rejects incoming HTTP requests with bodies exceeding the specified size limit."""

    def __init__(self, app, max_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > self.max_bytes:
                    logger.warning(
                        "PayloadSizeLimitMiddleware: Blocked request to %s (Content-Length: %d bytes, Max: %d bytes)",
                        request.url.path,
                        length,
                        self.max_bytes,
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "Payload Too Large",
                            "detail": f"Request body size ({length} bytes) exceeds maximum allowed limit of {self.max_bytes} bytes (2MB).",
                        },
                    )
            except ValueError:
                pass

        return await call_next(request)
