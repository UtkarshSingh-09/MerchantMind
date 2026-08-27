"""
Global error handling middleware for consistent API responses.
"""

import traceback
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catches unhandled exceptions and returns structured JSON errors."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            # Let FastAPI handle HTTP exceptions normally
            raise
        except Exception as exc:
            # Log the full traceback in development
            if settings.app_env == "development":
                traceback.print_exc()

            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "detail": str(exc) if settings.app_env == "development" else "An unexpected error occurred",
                    "type": type(exc).__name__,
                },
            )
