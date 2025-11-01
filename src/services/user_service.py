"""
User management service for business logic operations.

This module contains business logic for:
- Getting user information
- Updating user profiles
- User listing and filtering
- User deletion (admin only)
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AppException
from src.core.logging import get_logger
from src.models.user import User, UserRole
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserUpdate

# Initialize logger
logger = get_logger(__name__)


class UserService:
    """
    Service class for user management operations.

    Handles user CRUD operations and business logic.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        return await self.user_repo.get_by_id(user_id)

    async def get_user_by_uuid(self, user_uuid: UUID) -> Optional[User]:
        return await self.user_repo.get_by_uuid(user_uuid)

    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        is_verified: Optional[bool] = None,
    ) -> tuple[list[User], int]:
        users = await self.user_repo.get_all(skip=skip, limit=limit, role=role, is_verified=is_verified)
        total = await self.user_repo.count(role=role, is_verified=is_verified)
        return users, total

    async def update_user(self, user_uuid: UUID, user_data: UserUpdate, requesting_user: User) -> User:
        # Get user to update
        user = await self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise AppException("User not found", 404)

        # Check permissions
        if requesting_user.uuid != user_uuid and requesting_user.role != UserRole.ADMIN:
            raise AppException("Permission denied: You can only update your own profile", 403)

        # Check if email is being changed and if it's unique
        if user_data.email and user_data.email != user.email:
            if await self.user_repo.email_exists(user_data.email, exclude_user_id=user.id):
                raise AppException("Email already in use", 409)
            user.email = user_data.email

        # Update fields
        if user_data.first_name is not None:
            user.first_name = user_data.first_name

        if user_data.last_name is not None:
            user.last_name = user_data.last_name

        # Save changes
        user = await self.user_repo.update(user)

        return user

    async def delete_user(self, user_uuid: UUID, requesting_user: User) -> None:
        # Check if requesting user is admin
        if requesting_user.role != UserRole.ADMIN:
            raise AppException("Permission denied: Only admins can delete users", 403)

        # Get user to delete
        user = await self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise AppException("User not found", 404)

        # Prevent admin from deleting themselves
        if requesting_user.uuid == user_uuid:
            raise AppException("You cannot delete your own account", 403)

        # Delete user
        await self.user_repo.delete(user)

    async def deactivate_user(self, user_uuid: UUID, requesting_user: User) -> User:
        # Get user to deactivate
        user = await self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise AppException("User not found", 404)

        # Check permissions
        if requesting_user.uuid != user_uuid and requesting_user.role != UserRole.ADMIN:
            raise AppException("Permission denied", 403)

        # Deactivate user
        user.is_active = False
        return await self.user_repo.update(user)

    async def activate_user(self, user_uuid: UUID) -> User:
        user = await self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise AppException("User not found", 404)

        user.is_active = True
        return await self.user_repo.update(user)

    async def change_user_role(self, user_uuid: UUID, new_role: UserRole, requesting_user: User) -> User:
        # Check if requesting user is admin
        if requesting_user.role != UserRole.ADMIN:
            raise AppException("Permission denied: Only admins can change user roles", 403)

        # Get user
        user = await self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise AppException("User not found", 404)

        # Update role
        user.role = new_role
        return await self.user_repo.update(user)
