"""
User repository for database operations.

This module implements the data access layer for User entities,
providing CRUD operations and custom queries.

Note: This follows the Repository pattern to separate business logic
from data access, making the code more testable and maintainable.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    """
    Repository class for User entity operations.

    Handles all database interactions for users, including:
    - CRUD operations
    - Email uniqueness checks
    - Verification code management
    - Cleanup of unverified users
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    async def create(self, user: User) -> User:
        """
        Create a new user in the database.

        Args:
            user: User object to create

        Returns:
            User: Created user with assigned ID
        """
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID (internal use only).

        Args:
            user_id: User's ID

        Returns:
            User if found, None otherwise
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_uuid(self, user_uuid: UUID) -> Optional[User]:
        """
        Get user by UUID (for API use).

        Args:
            user_uuid: User's UUID

        Returns:
            User if found, None otherwise
        """
        result = await self.db.execute(select(User).where(User.uuid == user_uuid))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User's email

        Returns:
            User if found, None otherwise
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        is_verified: Optional[bool] = None,
    ) -> list[User]:
        """
        Get all users with optional filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            role: Filter by user role
            is_verified: Filter by verification status

        Returns:
            List of users
        """
        query = select(User)

        # Apply filters
        if role is not None:
            query = query.where(User.role == role)
        if is_verified is not None:
            query = query.where(User.is_verified == is_verified)

        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(
        self, role: Optional[UserRole] = None, is_verified: Optional[bool] = None
    ) -> int:
        """
        Count users with optional filtering.

        Args:
            role: Filter by user role
            is_verified: Filter by verification status

        Returns:
            Total count of users
        """
        query = select(func.count(User.id))

        # Apply filters
        if role is not None:
            query = query.where(User.role == role)
        if is_verified is not None:
            query = query.where(User.is_verified == is_verified)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def update(self, user: User) -> User:
        """
        Update user in the database.

        Args:
            user: User object with updated fields

        Returns:
            Updated user
        """
        user.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """
        Delete user from the database.

        Args:
            user: User object to delete
        """
        await self.db.delete(user)
        await self.db.commit()

    async def email_exists(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if email already exists in the database.

        Args:
            email: Email to check
            exclude_user_id: Optionally exclude a specific user ID (for updates)

        Returns:
            True if email exists, False otherwise
        """
        query = select(User).where(User.email == email)

        if exclude_user_id is not None:
            query = query.where(User.id != exclude_user_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def set_verification_code(self, user: User, code: str) -> User:
        """
        Set verification code for user.

        Args:
            user: User to update
            code: Verification code

        Returns:
            Updated user
        """
        user.verification_code = code
        user.verification_code_created_at = datetime.now(timezone.utc)
        return await self.update(user)

    async def verify_user(self, user: User) -> User:
        """
        Mark user as verified and clear verification code.

        Args:
            user: User to verify

        Returns:
            Updated user
        """
        user.is_verified = True
        user.verification_code = None
        user.verification_code_created_at = None
        return await self.update(user)

    async def get_unverified_users_older_than(self, days: int) -> list[User]:
        """
        Get unverified users created more than specified days ago.

        This is used for automatic cleanup of abandoned registrations.

        Args:
            days: Number of days threshold

        Returns:
            List of unverified users older than threshold
        """
        threshold_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            select(User).where(and_(User.is_verified.is_(False), User.created_at < threshold_date))
        )
        return list(result.scalars().all())

    async def bulk_delete(self, users: list[User]) -> int:
        """
        Delete multiple users at once.

        Args:
            users: List of users to delete

        Returns:
            Number of deleted users
        """
        count = 0
        for user in users:
            await self.db.delete(user)
            count += 1

        await self.db.commit()
        return count
