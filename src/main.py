"""
FastAPI application entry point.

This module creates and configures the FastAPI application instance,
including middleware, CORS, database initialization, and route registration.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import api_router
from src.core.config import settings
from src.core.handlers import register_exception_handlers
from src.core.logging import get_logger, setup_logging
from src.core.middleware import RequestLoggingMiddleware

# Setup logging before anything else
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    This replaces the deprecated @app.on_event decorators.
    """
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("📚 Documentation available at http://localhost:8000/docs")

    # Initialize database tables (in production, use Alembic migrations)
    # await init_db()  # Uncomment if you want auto table creation
    yield

    # Shutdown
    logger.info(f"👋 Shutting down {settings.APP_NAME}")


# Create FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Add request logging middleware (FIRST - to log all requests)
app.add_middleware(RequestLoggingMiddleware)


# Configure CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register exception handlers
register_exception_handlers(app)


# Include API router
app.include_router(api_router)


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information.

    Returns basic information about the API and available endpoints.
    """
    return {
        "message": "Welcome to Coffee Shop API",
        "version": settings.APP_VERSION,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns a simple status message indicating the API is running.

    Returns:
        dict: Health status
    """
    return {"status": "ok", "message": "API is running"}
