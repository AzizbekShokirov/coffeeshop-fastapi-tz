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

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User, UserRole


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
        self.db = db

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()  # Flush to get database-generated ID and UUID
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_uuid(self, user_uuid: UUID) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.uuid == user_uuid))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        is_verified: Optional[bool] = None,
    ) -> list[User]:
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

    async def count(self, role: Optional[UserRole] = None, is_verified: Optional[bool] = None) -> int:
        query = select(func.count(User.id))

        # Apply filters
        if role is not None:
            query = query.where(User.role == role)
        if is_verified is not None:
            query = query.where(User.is_verified == is_verified)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def update(self, user: User) -> User:
        user.updated_at = datetime.now(timezone.utc)
        self.db.add(user)  # Ensure the user is tracked by the session
        await self.db.flush()  # Flush to persist changes
        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.flush()  # Flush to ensure deletion is processed

    async def email_exists(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        query = select(User).where(User.email == email)

        if exclude_user_id is not None:
            query = query.where(User.id != exclude_user_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def set_verification_code(self, user: User, code: str) -> User:
        user.verification_code = code
        user.verification_code_created_at = datetime.now(timezone.utc)
        await self.db.flush()  # Flush to persist verification code
        return user

    async def verify_user(self, user: User) -> User:
        user.is_verified = True
        user.verification_code = None
        user.verification_code_created_at = None
        return await self.update(user)

    async def get_unverified_users_older_than(self, days: int) -> list[User]:
        threshold_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            select(User).where(and_(User.is_verified.is_(False), User.created_at < threshold_date))
        )
        return list(result.scalars().all())

    async def bulk_delete(self, users: list[User]) -> int:
        user_ids = [user.id for user in users]
        stmt = delete(User).where(User.id.in_(user_ids))
        result = await self.db.execute(stmt)
        await self.db.flush()  # Flush to ensure bulk deletion is processed
        return result.rowcount
