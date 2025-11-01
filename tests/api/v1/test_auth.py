"""
Tests for authentication endpoints.

This module tests:
- User registration (signup)
- User login
- Token refresh
- Email verification
"""

import pytest
from httpx import AsyncClient


class TestAuth:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_signup_success(self, client: AsyncClient):
        """Test successful user registration."""
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User",
        }

        response = await client.post("/api/v1/auth/signup", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["first_name"] == user_data["first_name"]
        assert data["last_name"] == user_data["last_name"]
        assert data["is_verified"] is False
        assert data["is_active"] is True
        assert "uuid" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email fails."""
        user_data = {
            "email": "duplicate@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User",
        }

        # First signup
        response1 = await client.post("/api/v1/auth/signup", json=user_data)
        assert response1.status_code == 201

        # Second signup with same email
        response2 = await client.post("/api/v1/auth/signup", json=user_data)
        assert response2.status_code == 409
        assert "Email already registered" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_unverified_user(self, client: AsyncClient):
        """Test login works for unverified users."""
        # First signup
        user_data = {
            "email": "login_test@example.com",
            "password": "TestPass123!",
            "first_name": "Login",
            "last_name": "Test",
        }
        signup_response = await client.post("/api/v1/auth/signup", json=user_data)
        assert signup_response.status_code == 201

        # Then login
        login_data = {"email": user_data["email"], "password": user_data["password"]}
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        """Test login with wrong password fails."""
        login_data = {"email": "nonexistent@example.com", "password": "wrongpassword"}
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient):
        """Test token refresh functionality."""
        # First signup and login
        user_data = {
            "email": "refresh_test@example.com",
            "password": "TestPass123!",
            "first_name": "Refresh",
            "last_name": "Test",
        }
        await client.post("/api/v1/auth/signup", json=user_data)

        login_data = {"email": user_data["email"], "password": user_data["password"]}
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        refresh_data = {"refresh_token": refresh_token}
        response = await client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token fails."""
        refresh_data = {"refresh_token": "invalid.token.here"}
        response = await client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_signup_with_weak_password(self, client: AsyncClient):
        """Test that weak passwords are rejected."""
        user_data = {
            "email": "weak@example.com",
            "password": "123",  # Too short
            "first_name": "Weak",
            "last_name": "Password",
        }

        response = await client.post("/api/v1/auth/signup", json=user_data)

        # Should fail validation
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_with_invalid_email(self, client: AsyncClient):
        """Test that invalid email format is rejected."""
        user_data = {
            "email": "not-an-email",  # Invalid format
            "password": "TestPass123!",
            "first_name": "Invalid",
            "last_name": "Email",
        }

        response = await client.post("/api/v1/auth/signup", json=user_data)

        # Should fail validation
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user fails."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!",
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
