"""
Logging configuration for the application.

This module provides:
- Structured logging setup
- JSON logging for production
- Colored console logging for development
- Request/response logging
- Error tracking
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to console output for better readability.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        # Format the message
        formatted = super().format(record)

        # Reset levelname for potential future use
        record.levelname = levelname

        return formatted


class RequestLogger:
    """
    Context manager for logging API requests with timing.
    """

    def __init__(
        self, logger: logging.Logger, endpoint: str, method: str, user_id: int | None = None
    ):
        self.logger = logger
        self.endpoint = endpoint
        self.method = method
        self.user_id = user_id
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(
            "📥 Request started",
            extra={
                "method": self.method,
                "endpoint": self.endpoint,
                "user_id": self.user_id,
            },
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds() * 1000

        if exc_type is None:
            self.logger.info(
                "✅ Request completed",
                extra={
                    "method": self.method,
                    "endpoint": self.endpoint,
                    "user_id": self.user_id,
                    "duration_ms": round(duration, 2),
                    "status": "success",
                },
            )
        else:
            self.logger.error(
                "❌ Request failed",
                extra={
                    "method": self.method,
                    "endpoint": self.endpoint,
                    "user_id": self.user_id,
                    "duration_ms": round(duration, 2),
                    "error_type": exc_type.__name__,
                    "error_message": str(exc_val),
                },
            )


def setup_logging() -> None:
    """
    Configure application logging.

    Sets up:
    - Console handler with colored output (development)
    - File handler for persistent logs
    - Different log levels based on DEBUG setting
    - Structured logging format
    """

    # Determine log level
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console Handler (with colors in development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if settings.DEBUG:
        # Colored format for development
        console_format = ColoredFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # Simple format for production
        console_format = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File Handler (always active)
    file_handler = logging.FileHandler(
        logs_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log", encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)

    # Error File Handler (only errors and above)
    error_handler = logging.FileHandler(
        logs_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log", encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    root_logger.addHandler(error_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Log startup message
    root_logger.info("=" * 80)
    root_logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    root_logger.info(f"📊 Log Level: {logging.getLevelName(log_level)}")
    root_logger.info(f"🔧 Debug Mode: {settings.DEBUG}")
    root_logger.info("=" * 80)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Usually __name__ of the calling module

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("User created", extra={"user_id": 123})
    """
    return logging.getLogger(name)


def log_request(endpoint: str, method: str, user_id: int | None = None) -> RequestLogger:
    """
    Create a request logger context manager.

    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        user_id: ID of authenticated user (if any)

    Returns:
        RequestLogger context manager

    Example:
        with log_request("/api/v1/users", "POST", user_id=123):
            # Your endpoint logic
            pass
    """
    logger = get_logger("api.request")
    return RequestLogger(logger, endpoint, method, user_id)


def log_error(
    logger: logging.Logger, error: Exception, context: dict[str, Any] | None = None
) -> None:
    """
    Log an error with context information.

    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context information

    Example:
        try:
            result = await service.create_user(data)
        except ValueError as e:
            log_error(logger, e, {"user_data": data})
            raise
    """
    context = context or {}
    logger.error(
        f"Error occurred: {str(error)}",
        extra={"error_type": type(error).__name__, "error_message": str(error), **context},
        exc_info=True,
    )
