"""
Middleware for request/response logging and metrics.

This module provides middleware for:
- Automatic request/response logging
- Request timing/metrics
- Error tracking
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all incoming requests and outgoing responses.

    Logs include:
    - HTTP method and path
    - Request duration
    - Response status code
    - Client IP
    - User agent
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request and log details.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response from the handler
        """
        # Start timing
        start_time = time.time()

        # Get request details
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Log request
        logger.info(
            f"📥 {method} {path}",
            extra={
                "method": method,
                "path": path,
                "client_ip": client_ip,
                "user_agent": user_agent,
            },
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = (time.time() - start_time) * 1000  # Convert to ms

            # Log response
            logger.info(
                f"📤 {method} {path} - {response.status_code} ({duration:.2f}ms)",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration, 2),
                    "client_ip": client_ip,
                },
            )

            return response

        except Exception as e:
            # Calculate duration
            duration = (time.time() - start_time) * 1000

            # Log error
            logger.error(
                f"❌ {method} {path} - ERROR ({duration:.2f}ms): {str(e)}",
                extra={
                    "method": method,
                    "path": path,
                    "duration_ms": round(duration, 2),
                    "client_ip": client_ip,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            # Re-raise the exception
            raise
