"""
Authentication service for user registration, login, and verification.

This module contains business logic for:
- User signup and registration
- Login and token generation
- Email/SMS verification
- Token refresh

Note: In a production environment, email/SMS sending would be integrated
with services like SendGrid, Twilio, AWS SES, etc. For this implementation,
verification codes are logged to console for demonstration purposes.
"""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import AppException
from src.core.logging import get_logger
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from src.models.user import User, UserRole
from src.repositories.user_repository import UserRepository
from src.schemas.user import Token, UserLogin, UserSignup

# Initialize logger
logger = get_logger(__name__)


class AuthService:
    """
    Service class for auth management operations.

    Handles user authentication and authorization logic.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def signup(self, user_data: UserSignup) -> tuple[User, str]:
        # Check if email already exists
        if await self.user_repo.email_exists(user_data.email):
            raise AppException("Email already registered", 409)

        # Hash password
        hashed_password = get_password_hash(user_data.password)

        # Create user
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=UserRole.USER,
            is_verified=False,
            is_active=True,
        )

        # Save user to database
        user = await self.user_repo.create(user)

        # Generate 6-digit verification code
        verification_code = self._generate_verification_code()
        await self.user_repo.set_verification_code(user, verification_code)

        # For now log code to console
        self._send_verification_code(user.email, verification_code)

        return user, verification_code

    async def login(self, login_data: UserLogin) -> Token:
        # Find user by email
        user = await self.user_repo.get_by_email(login_data.email)
        if not user:
            raise AppException("Invalid email or password", 401)

        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise AppException("Invalid email or password", 401)

        # Check if user is active
        if not user.is_active:
            raise AppException("User account is deactivated", 403)

        # Generate tokens
        access_token = create_access_token(data={"sub": str(user.uuid), "email": user.email})
        refresh_token = create_refresh_token(data={"sub": str(user.uuid)})

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",  # nosec B106
        )

    async def verify_user(self, user_uuid: UUID, verification_code: str) -> User:
        user = await self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise AppException("User not found", 404)

        # Check if already verified
        if user.is_verified:
            raise AppException("User already verified", 400)

        # Check if verification code matches
        if user.verification_code != verification_code:
            raise AppException("Invalid verification code", 400)

        # Check if code has expired
        if user.verification_code_created_at:
            expiry_time = user.verification_code_created_at + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRATION)
            if datetime.now(timezone.utc) > expiry_time:
                raise AppException("Verification code has expired", 400)

        # Mark user as verified
        user = await self.user_repo.verify_user(user)

        print(f"✅ User {user.email} has been verified successfully!")

        return user

    async def refresh_access_token(self, refresh_token: str) -> Token:
        # Decode token
        payload = decode_token(refresh_token)
        if not payload:
            raise AppException("Invalid refresh token", 401)

        # Check token type
        if payload.get("type") != "refresh":
            raise AppException("Invalid token type", 401)

        # Get user UUID from token
        user_uuid_str = payload.get("sub")
        if not user_uuid_str:
            raise AppException("Invalid token payload", 401)

        # Find user by UUID
        user = await self.user_repo.get_by_uuid(UUID(user_uuid_str))
        if not user:
            raise AppException("User not found", 404)

        if not user.is_active:
            raise AppException("User account is deactivated", 403)

        # Generate new tokens
        access_token = create_access_token(data={"sub": str(user.uuid), "email": user.email})
        new_refresh_token = create_refresh_token(data={"sub": str(user.uuid)})

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",  # nosec B106
        )

    async def resend_verification_code(self, user_uuid: UUID) -> str:
        user = await self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise AppException("User not found", 404)

        if user.is_verified:
            raise AppException("User already verified", 400)

        # Generate new verification code
        verification_code = self._generate_verification_code()
        await self.user_repo.set_verification_code(user, verification_code)

        # Send verification code
        self._send_verification_code(user.email, verification_code)

        return verification_code

    def _generate_verification_code(self) -> str:
        return str(secrets.randbelow(1000000)).zfill(6)

    def _send_verification_code(self, email: str, code: str) -> None:
        print("\n" + "=" * 60)
        print("📧 VERIFICATION CODE (Console Output for Demo)")
        print("=" * 60)
        print(f"To: {email}")
        print(f"Verification Code: {code}")
        print(f"Valid for: {settings.VERIFICATION_CODE_EXPIRATION} minutes")
        print("=" * 60 + "\n")
