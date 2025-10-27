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

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import Token, UserLogin, UserSignup

# Initialize logger
logger = get_logger(__name__)


class AuthService:
    """
    Service class for authentication operations.

    Handles user registration, login, verification, and token management.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db
        self.user_repo = UserRepository(db)

    async def signup(self, user_data: UserSignup) -> tuple[User, str]:
        """
        Register a new user.

        Process:
        1. Check if email already exists
        2. Hash password
        3. Create user with is_verified=False
        4. Generate verification code
        5. Send verification code (logged to console for demo)

        Args:
            user_data: User registration data

        Returns:
            Tuple of (created user, verification code)

        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        if await self.user_repo.email_exists(user_data.email):
            raise ValueError("Email already registered")

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
        """
        Authenticate user and generate tokens.

        Process:
        1. Find user by email
        2. Verify password
        3. Check if user is active
        4. Generate access and refresh tokens

        Args:
            login_data: User login credentials

        Returns:
            Token object with access and refresh tokens

        Raises:
            ValueError: If credentials are invalid or user not found
        """
        # Find user by email
        user = await self.user_repo.get_by_email(login_data.email)
        if not user:
            raise ValueError("Invalid email or password")

        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise ValueError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            raise ValueError("User account is deactivated")

        # Generate tokens
        access_token = create_access_token(data={"sub": str(user.uuid), "email": user.email})
        refresh_token = create_refresh_token(data={"sub": str(user.uuid)})

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",  # nosec B106
        )

    async def verify_user(self, user_uuid: UUID, verification_code: str) -> User:
        """
        Verify user's email/phone with verification code.

        Process:
        1. Find user by UUID
        2. Check if already verified
        3. Validate verification code
        4. Check if code has expired
        5. Mark user as verified

        Args:
            user_uuid: User's UUID
            verification_code: 6-digit verification code

        Returns:
            Verified user

        Raises:
            ValueError: If verification fails
        """
        user = await self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise ValueError("User not found")

        # Check if already verified
        if user.is_verified:
            raise ValueError("User already verified")

        # Check if verification code matches
        if user.verification_code != verification_code:
            raise ValueError("Invalid verification code")

        # Check if code has expired
        if user.verification_code_created_at:
            expiry_time = user.verification_code_created_at + timedelta(
                minutes=settings.VERIFICATION_CODE_EXPIRATION
            )
            if datetime.now(timezone.utc) > expiry_time:
                raise ValueError("Verification code has expired")

        # Mark user as verified
        user = await self.user_repo.verify_user(user)

        print(f"✅ User {user.email} has been verified successfully!")

        return user

    async def refresh_access_token(self, refresh_token: str) -> Token:
        """
        Generate new access token using refresh token.

        Process:
        1. Decode and validate refresh token
        2. Check token type
        3. Find user
        4. Generate new access token

        Args:
            refresh_token: Valid refresh token

        Returns:
            New token pair

        Raises:
            ValueError: If refresh token is invalid
        """
        # Decode token
        payload = decode_token(refresh_token)
        if not payload:
            raise ValueError("Invalid refresh token")

        # Check token type
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        # Get user UUID from token
        user_uuid_str = payload.get("sub")
        if not user_uuid_str:
            raise ValueError("Invalid token payload")

        # Find user by UUID
        user = await self.user_repo.get_by_uuid(UUID(user_uuid_str))
        if not user:
            raise ValueError("User not found")

        if not user.is_active:
            raise ValueError("User account is deactivated")

        # Generate new tokens
        access_token = create_access_token(data={"sub": str(user.uuid), "email": user.email})
        new_refresh_token = create_refresh_token(data={"sub": str(user.uuid)})

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",  # nosec B106
        )

    async def resend_verification_code(self, user_uuid: UUID) -> str:
        """
        Resend verification code to user.

        Args:
            user_uuid: User's UUID

        Returns:
            New verification code

        Raises:
            ValueError: If user not found or already verified
        """
        user = await self.user_repo.get_by_uuid(user_uuid)
        if not user:
            raise ValueError("User not found")

        if user.is_verified:
            raise ValueError("User already verified")

        # Generate new verification code
        verification_code = self._generate_verification_code()
        await self.user_repo.set_verification_code(user, verification_code)

        # Send verification code
        self._send_verification_code(user.email, verification_code)

        return verification_code

    def _generate_verification_code(self) -> str:
        """
        Generate a random 6-digit verification code.

        Returns:
            6-digit verification code as string
        """
        return str(secrets.randbelow(1000000)).zfill(6)

    def _send_verification_code(self, email: str, code: str) -> None:
        """
        Send verification code to user.

        Args:
            email: User's email
            code: Verification code
        """
        print("\n" + "=" * 60)
        print("📧 VERIFICATION CODE (Console Output for Demo)")
        print("=" * 60)
        print(f"To: {email}")
        print(f"Verification Code: {code}")
        print(f"Valid for: {settings.VERIFICATION_CODE_EXPIRATION} minutes")
        print("=" * 60 + "\n")
