"""
API v1 Router.

This module registers all v1 endpoints and creates the main API router.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users

# Create API v1 router
api_router = APIRouter(prefix="/api/v1")

# Include authentication endpoints
api_router.include_router(auth.router)

# Include user management endpoints
api_router.include_router(users.router)
