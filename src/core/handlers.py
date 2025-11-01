"""
Exception handlers for FastAPI.

This module provides exception handlers that return clean status codes and messages.
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions import AppException


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": "Validation error", "errors": exc.errors()})

    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_error_handler(request: Request, exc: PydanticValidationError):
        return JSONResponse(status_code=422, content={"detail": "Validation error", "errors": exc.errors()})

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        return JSONResponse(status_code=409, content={"detail": "Resource already exists or constraint violation"})

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        return JSONResponse(status_code=500, content={"detail": "Database error occurred"})

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
