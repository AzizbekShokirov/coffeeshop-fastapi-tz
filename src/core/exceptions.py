"""
Application exceptions for FastAPI.

This module defines a simple exception system for the application.
"""

import logging

logger = logging.getLogger(__name__)


class AppException(Exception):
    """
    Base application exception.

    All application exceptions should inherit from this class or use it directly.
    """

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)
