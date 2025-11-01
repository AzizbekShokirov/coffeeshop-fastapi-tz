"""
API v1 Router.

This module registers all v1 endpoints and creates the main API router.
"""

from fastapi import APIRouter

from src.api.v1.endpoints import auth_routes, user_routes

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_routes.router)
api_router.include_router(user_routes.router)
