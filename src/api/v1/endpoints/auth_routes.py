"""
Authentication endpoints.

This module provides endpoints for:
- User registration (signup)
- User login (authentication)
- Email/SMS verification
- Token refresh
"""

from fastapi import APIRouter, status

from src.core.config import settings
from src.core.dependencies import CurrentUser, DatabaseSession
from src.core.logging import get_logger
from src.schemas.user import (
    MessageResponse,
    Token,
    TokenRefresh,
    UserLogin,
    UserResponse,
    UserSignup,
    VerificationRequest,
)
from src.services.auth_service import AuthService

# Initialize logger
logger = get_logger(__name__)


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=f"""
    Register a new user account in the system.

    After successful registration:
    - User receives status "not verified"
    - A 6-digit verification code is generated and sent (logged to console for demo)
    - User must verify within {settings.VERIFICATION_CODE_EXPIRATION} minutes
    - Unverified accounts are automatically deleted after 2 days

    Required fields:
    - email: Valid email address (must be unique)
    - password: Minimum 8 characters

    Optional fields:
    - first_name: User's first name
    - last_name: User's last name
    """,
)
async def signup(
    user_data: UserSignup,
    db: DatabaseSession,
):
    """Create a new user account."""
    logger.info(f"New signup request for email: {user_data.email}")

    auth_service = AuthService(db)

    user, verification_code = await auth_service.signup(user_data)

    logger.info(
        "User registered successfully",
        extra={"user_uuid": str(user.uuid), "email": user.email, "action": "signup"},
    )

    # In production, verification code is sent via email/SMS
    # For demo, it's logged to console
    logger.debug(f"Verification code for {user.email}: {verification_code}")

    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Login to get access tokens",
    description=f"""
    Authenticate user and receive JWT tokens.

    Returns:
        - access_token: Short-lived token ({settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes) for API requests
    - refresh_token: Long-lived token ({settings.REFRESH_TOKEN_EXPIRE_DAYS} days) to refresh access tokens
    - token_type: "bearer"

    Note: User must be active to login. Verification is not required for login,
    but some endpoints may require verified status.
    """,
)
async def login(
    login_data: UserLogin,
    db: DatabaseSession,
):
    """Authenticate user and generate tokens."""
    logger.info(f"Login attempt for email: {login_data.email}")

    auth_service = AuthService(db)

    token = await auth_service.login(login_data)

    logger.info("User logged in successfully", extra={"email": login_data.email, "action": "login"})

    return token


@router.post(
    "/verify",
    response_model=MessageResponse,
    summary="Verify user email/phone with code",
    description=f"""
    Verify user account using the 6-digit code sent during registration.

    Verification process:
    1. User provides the verification code received via email/SMS
    2. System validates the code against database
    3. Checks if code has expired ({settings.VERIFICATION_CODE_EXPIRATION} minutes)
    4. Marks user as verified on success

    After successful verification:
    - User status changes to "verified"
    - Verification code is cleared from database
    - User can access all verified-only endpoints
    """,
)
async def verify(
    verification_data: VerificationRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """Verify user account with verification code."""
    logger.info(
        f"Verification attempt for user: {current_user.email}",
        extra={"user_uuid": str(current_user.uuid)},
    )

    auth_service = AuthService(db)

    await auth_service.verify_user(current_user.uuid, verification_data.verification_code)

    logger.info(
        "User verified successfully",
        extra={
            "user_uuid": str(current_user.uuid),
            "email": current_user.email,
            "action": "verify",
        },
    )

    return MessageResponse(
        message="Account verified successfully",
        detail="Your account has been verified. You now have full access.",
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="""
    Generate a new access token using a refresh token.

    When the access token expires, use this endpoint to get a new one
    without requiring the user to login again.

    Process:
    1. Provide valid refresh token
    2. System validates refresh token
    3. Returns new access token and refresh token pair

    Note: Both access and refresh tokens are regenerated for security.
    """,
)
async def refresh_token(
    refresh_data: TokenRefresh,
    db: DatabaseSession,
):
    """Refresh access token using refresh token."""
    logger.info("Token refresh attempt")

    auth_service = AuthService(db)

    token = await auth_service.refresh_access_token(refresh_data.refresh_token)

    logger.info("Token refreshed successfully", extra={"action": "refresh_token"})

    return token


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend verification code",
    description="""
    Resend verification code to user's email/phone.

    Use this endpoint when:
    - User didn't receive the original code
    - Verification code has expired
    - User deleted the original message

    A new 6-digit code will be generated and sent.
    The old code becomes invalid.
    """,
)
async def resend_verification(
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """Resend verification code to user."""
    logger.info(
        f"Resend verification code request for user: {current_user.email}",
        extra={"user_uuid": str(current_user.uuid)},
    )

    auth_service = AuthService(db)

    await auth_service.resend_verification_code(current_user.uuid)

    logger.info(
        "Verification code resent successfully",
        extra={
            "user_uuid": str(current_user.uuid),
            "email": current_user.email,
            "action": "resend_verification",
        },
    )

    return MessageResponse(
        message="Verification code resent successfully",
        detail="A new verification code has been sent to your email/phone.",
    )
