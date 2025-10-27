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

from app.core.logging import get_logger
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate

# Initialize logger
logger = get_logger(__name__)


class UserService:
    """
    Service class for user management operations.

    Handles user CRUD operations and business logic.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db
        self.user_repo = UserRepository(db)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID (internal use only).

        Args:
            user_id: User's ID

        Returns:
            User if found, None otherwise
        """
        return await self.user_repo.get_by_id(user_id)

    async def get_user_by_uuid(self, user_uuid: UUID) -> Optional[User]:
        """
        Get user by UUID (for API use).

        Args:
            user_uuid: User's UUID

        Returns:
            User if found, None otherwise
        """
        return await self.user_repo.get_by_uuid(user_uuid)

    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        is_verified: Optional[bool] = None,
    ) -> tuple[list[User], int]:
        """
        Get list of users with pagination and filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            role: Filter by user role
            is_verified: Filter by verification status

        Returns:
            Tuple of (users list, total count)
        """
        users = await self.user_repo.get_all(
            skip=skip, limit=limit, role=role, is_verified=is_verified
        )
        total = await self.user_repo.count(role=role, is_verified=is_verified)
        return users, total

    async def update_user(
        self, user_uuid: UUID, user_data: UserUpdate, requesting_user: User
    ) -> User:
        """
        Update user information.

        Users can update their own profile.
        Admins can update any user's profile.

        Args:
            user_uuid: UUID of user to update
            user_data: Updated user data
            requesting_user: User making the request

        Returns:
            Updated user

        Raises:
            ValueError: If user not found or permission denied
        """
        # Get user to update
        user = await self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise ValueError("User not found")

        # Check permissions
        if requesting_user.uuid != user_uuid and requesting_user.role != UserRole.ADMIN:
            raise ValueError("Permission denied: You can only update your own profile")

        # Check if email is being changed and if it's unique
        if user_data.email and user_data.email != user.email:
            if await self.user_repo.email_exists(user_data.email, exclude_user_id=user.id):
                raise ValueError("Email already in use")
            user.email = user_data.email

        # Update fields
        if user_data.first_name is not None:
            user.first_name = user_data.first_name

        if user_data.last_name is not None:
            user.last_name = user_data.last_name

        # Save changes
        return await self.user_repo.update(user)

    async def delete_user(self, user_uuid: UUID, requesting_user: User) -> None:
        """
        Delete user (admin only).

        Args:
            user_uuid: UUID of user to delete
            requesting_user: User making the request

        Raises:
            ValueError: If user not found or permission denied
        """
        # Check if requesting user is admin
        if requesting_user.role != UserRole.ADMIN:
            raise ValueError("Permission denied: Only admins can delete users")

        # Get user to delete
        user = await self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise ValueError("User not found")

        # Prevent admin from deleting themselves
        if requesting_user.uuid == user_uuid:
            raise ValueError("You cannot delete your own account")

        # Delete user
        await self.user_repo.delete(user)

    async def deactivate_user(self, user_uuid: UUID, requesting_user: User) -> User:
        """
        Deactivate user account (soft delete).

        Args:
            user_uuid: UUID of user to deactivate
            requesting_user: User making the request

        Returns:
            Deactivated user

        Raises:
            ValueError: If user not found or permission denied
        """
        # Get user to deactivate
        user = await self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise ValueError("User not found")

        # Check permissions
        if requesting_user.uuid != user_uuid and requesting_user.role != UserRole.ADMIN:
            raise ValueError("Permission denied")

        # Deactivate user
        user.is_active = False
        return await self.user_repo.update(user)

    async def activate_user(self, user_uuid: UUID) -> User:
        """
        Activate user account (admin only).

        Args:
            user_uuid: UUID of user to activate

        Returns:
            Activated user

        Raises:
            ValueError: If user not found
        """
        user = await self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise ValueError("User not found")

        user.is_active = True
        return await self.user_repo.update(user)

    async def change_user_role(
        self, user_uuid: UUID, new_role: UserRole, requesting_user: User
    ) -> User:
        """
        Change user role (admin only).

        Args:
            user_uuid: UUID of user to update
            new_role: New role to assign
            requesting_user: User making the request

        Returns:
            Updated user

        Raises:
            ValueError: If user not found or permission denied
        """
        # Check if requesting user is admin
        if requesting_user.role != UserRole.ADMIN:
            raise ValueError("Permission denied: Only admins can change user roles")

        # Get user
        user = await self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise ValueError("User not found")

        # Update role
        user.role = new_role
        return await self.user_repo.update(user)
