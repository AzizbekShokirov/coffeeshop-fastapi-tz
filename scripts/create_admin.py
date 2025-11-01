#!/usr/bin/env python
"""
Script to create an initial admin user.

Usage:
    python scripts/create_admin.py

Or with Docker:
    docker compose -f local.yml exec api python scripts/create_admin.py
"""

import asyncio
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.core.database import async_session_factory
from src.core.security import get_password_hash
from src.models.user import User, UserRole
from src.repositories.user_repository import UserRepository


async def create_admin_user():
    """Create an initial admin user."""

    # Default admin credentials
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD

    print("=" * 60)
    print("Creating Initial Admin User")
    print("=" * 60)

    async with async_session_factory() as db:
        async with db.begin():  # Explicit transaction
            user_repo = UserRepository(db)

            # Check if admin already exists
            existing_admin = await user_repo.get_by_email(admin_email)
            if existing_admin:
                print(f"⚠️  Admin user already exists: {admin_email}")
                print(f"   User ID: {existing_admin.id}")
                print(f"   UUID: {existing_admin.uuid}")
                print(f"   Role: {existing_admin.role}")
                print(f"   Verified: {existing_admin.is_verified}")
                return

            # Create admin user
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                first_name="Admin",
                last_name="User",
                role=UserRole.ADMIN,
                is_verified=True,  # Admin is pre-verified
                is_active=True,
            )

            admin_user = await user_repo.create(admin_user)
            # Transaction commits automatically when exiting db.begin()

        print("✅ Admin user created successfully!")
        print()
        print("Credentials:")
        print(f"   Email:    {admin_email}")
        print(f"   Password: {admin_password}")
        print(f"   UUID:     {admin_user.uuid}")
        print()
        print("⚠️  IMPORTANT: Change this password immediately in production!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(create_admin_user())
