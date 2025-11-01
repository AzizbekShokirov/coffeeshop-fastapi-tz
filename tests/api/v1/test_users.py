"""
Tests for user management endpoints.

This module tests:
- Get current user profile
- Update user profile
- User listing (admin)
- User deactivation/activation
- Role changes
"""

import pytest
from httpx import AsyncClient


class TestUsers:
    """Test user management endpoints."""

    @pytest.mark.asyncio
    async def test_get_current_user_profile(self, client: AsyncClient):
        """Test getting current user profile."""
        # First create and login a user
        user_data = {
            "email": "profile_test@example.com",
            "password": "TestPass123!",
            "first_name": "Profile",
            "last_name": "Test",
        }
        await client.post("/api/v1/auth/signup", json=user_data)

        login_data = {"email": user_data["email"], "password": user_data["password"]}
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        access_token = login_response.json()["access_token"]

        # Get profile
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["first_name"] == user_data["first_name"]
        assert data["last_name"] == user_data["last_name"]
        assert data["is_verified"] is False

    @pytest.mark.asyncio
    async def test_update_user_profile(self, client: AsyncClient):
        """Test updating user profile."""
        # Create and login user
        user_data = {
            "email": "update_test@example.com",
            "password": "TestPass123!",
            "first_name": "Update",
            "last_name": "Test",
        }
        await client.post("/api/v1/auth/signup", json=user_data)

        login_data = {"email": user_data["email"], "password": user_data["password"]}
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        access_token = login_response.json()["access_token"]

        # Get user profile to get UUID
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = await client.get("/api/v1/users/me", headers=headers)
        user_uuid = profile_response.json()["uuid"]

        # Update profile using PATCH /{user_uuid}
        update_data = {"first_name": "Updated", "last_name": "Name"}
        response = await client.patch(f"/api/v1/users/{user_uuid}", json=update_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["email"] == user_data["email"]

    @pytest.mark.asyncio
    async def test_get_users_admin_only(self, client: AsyncClient):
        """Test that only admins can list users."""
        # Create regular user
        user_data = {
            "email": "regular@example.com",
            "password": "TestPass123!",
            "first_name": "Regular",
            "last_name": "User",
        }
        await client.post("/api/v1/auth/signup", json=user_data)

        login_data = {"email": user_data["email"], "password": user_data["password"]}
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        access_token = login_response.json()["access_token"]

        # Try to get users list
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get("/api/v1/users", headers=headers)

        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_user_cannot_update_others_profile(self, client: AsyncClient):
        """Test that users cannot update other users' profiles."""
        # Create two users
        user1_data = {
            "email": "user1@example.com",
            "password": "TestPass123!",
            "first_name": "User",
            "last_name": "One",
        }
        user2_data = {
            "email": "user2@example.com",
            "password": "TestPass123!",
            "first_name": "User",
            "last_name": "Two",
        }
        await client.post("/api/v1/auth/signup", json=user1_data)
        await client.post("/api/v1/auth/signup", json=user2_data)

        # Login as user1
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": user1_data["email"], "password": user1_data["password"]},
        )
        access_token = login_response.json()["access_token"]

        # Get user2's UUID by logging in as user2
        login2_response = await client.post(
            "/api/v1/auth/login",
            json={"email": user2_data["email"], "password": user2_data["password"]},
        )
        access_token2 = login2_response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {access_token2}"}
        profile2_response = await client.get("/api/v1/users/me", headers=headers2)
        user2_uuid = profile2_response.json()["uuid"]

        # Try to update user2's profile while logged in as user1 (should fail)
        headers = {"Authorization": f"Bearer {access_token}"}
        update_data = {"first_name": "Hacked"}
        response = await client.patch(f"/api/v1/users/{user2_uuid}", json=update_data, headers=headers)

        assert response.status_code == 403
        assert "You can only update your own profile" in response.json()["detail"]

        # Verify user1 can update their own profile
        profile_response = await client.get("/api/v1/users/me", headers=headers)
        user1_uuid = profile_response.json()["uuid"]

        update_data = {"first_name": "UpdatedSelf"}
        response = await client.patch(f"/api/v1/users/{user1_uuid}", json=update_data, headers=headers)

        assert response.status_code == 200
        assert response.json()["first_name"] == "UpdatedSelf"

    @pytest.mark.asyncio
    async def test_update_user_with_duplicate_email(self, client: AsyncClient):
        """Test that updating to an existing email fails."""
        # Create two users
        user1_data = {
            "email": "unique1@example.com",
            "password": "TestPass123!",
            "first_name": "User",
            "last_name": "One",
        }
        user2_data = {
            "email": "unique2@example.com",
            "password": "TestPass123!",
            "first_name": "User",
            "last_name": "Two",
        }
        await client.post("/api/v1/auth/signup", json=user1_data)
        await client.post("/api/v1/auth/signup", json=user2_data)

        # Login as user1
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": user1_data["email"], "password": user1_data["password"]},
        )
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Get user1's UUID
        profile_response = await client.get("/api/v1/users/me", headers=headers)
        user1_uuid = profile_response.json()["uuid"]

        # Try to update user1's email to user2's email (should fail)
        update_data = {"email": "unique2@example.com"}
        response = await client.patch(f"/api/v1/users/{user1_uuid}", json=update_data, headers=headers)

        assert response.status_code == 409
        assert "Email already in use" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test that endpoints require authentication."""
        # Try to get profile without token
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 403

        # Try to get users list without token
        response = await client.get("/api/v1/users")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_uuid_format(self, client: AsyncClient):
        """Test that invalid UUID returns proper error."""
        # Create and login user
        user_data = {
            "email": "uuid_test@example.com",
            "password": "TestPass123!",
            "first_name": "UUID",
            "last_name": "Test",
        }
        await client.post("/api/v1/auth/signup", json=user_data)

        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": user_data["email"], "password": user_data["password"]},
        )
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Try to update with invalid UUID
        update_data = {"first_name": "Updated"}
        response = await client.patch("/api/v1/users/invalid-uuid", json=update_data, headers=headers)

        assert response.status_code == 422  # Validation error
