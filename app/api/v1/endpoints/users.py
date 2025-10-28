"""
User management endpoints.

This module provides endpoints for:
- Get current user profile
- List all users (admin only)
- Get user by UUID (admin only)
- Update user profile
- Delete user (admin only)
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import AdminUser, CurrentUser, DatabaseSession
from app.core.logging import get_logger
from app.schemas.user import MessageResponse, UserListResponse, UserResponse, UserUpdate
from app.services.user_service import UserService

# Initialize logger
logger = get_logger(__name__)


router = APIRouter(prefix="/users", tags=["User Management"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="""
    Get the profile information of the currently authenticated user.

    Returns complete user information including:
    - Basic profile (email, name)
    - Role and permissions
    - Verification status
    - Account creation date

    Note: Any authenticated user can access their own profile.
    """,
)
async def get_current_user_profile(
    current_user: CurrentUser,
):
    """Get current user's profile."""
    logger.debug(
        "User profile request",
        extra={"user_uuid": str(current_user.uuid), "email": current_user.email},
    )
    return current_user


@router.get(
    "",
    response_model=UserListResponse,
    summary="Get list of all users (Admin only)",
    description="""
    Retrieve a paginated list of all users in the system.

    Admin access required

    Features:
    - Pagination support (page, page_size)
    - Filter by role (user, admin)
    - Filter by verification status
    - Ordered by creation date (newest first)

    Use this endpoint for:
    - User management dashboards
    - Generating user reports
    - Monitoring new registrations
    """,
)
async def get_users(
    admin: AdminUser,
    db: DatabaseSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    is_verified: bool | None = Query(None, description="Filter by verification status"),
):
    """Get all users (admin only)."""
    logger.info(
        "Admin user list request",
        extra={
            "admin_uuid": str(admin.uuid),
            "page": page,
            "page_size": page_size,
            "is_verified_filter": is_verified,
        },
    )

    user_service = UserService(db)

    # Calculate skip
    skip = (page - 1) * page_size

    # Get users
    users, total = await user_service.get_users(skip=skip, limit=page_size, is_verified=is_verified)

    logger.info(
        f"Retrieved {len(users)} users (total: {total})",
        extra={"admin_uuid": str(admin.uuid), "count": len(users), "total": total},
    )

    return UserListResponse(users=users, total=total, page=page, page_size=page_size)


@router.get(
    "/{user_uuid}",
    response_model=UserResponse,
    summary="Get user by UUID (Admin only)",
    description="""
    Retrieve detailed information about a specific user by their UUID.

    Admin access required

    Use this endpoint to:
    - View user details for support requests
    - Verify user information
    - Investigate account issues
    """,
)
async def get_user_by_uuid(
    user_uuid: UUID,
    admin: AdminUser,
    db: DatabaseSession,
):
    """Get user by UUID (admin only)."""
    logger.info(
        f"Admin requesting user by UUID: {user_uuid}",
        extra={"admin_uuid": str(admin.uuid), "requested_user_uuid": str(user_uuid)},
    )

    user_service = UserService(db)

    user = await user_service.get_user_by_uuid(user_uuid)

    if not user:
        logger.warning(
            f"User not found with UUID: {user_uuid}",
            extra={"admin_uuid": str(admin.uuid), "requested_user_uuid": str(user_uuid)},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with UUID {user_uuid} not found"
        )

    return user


@router.patch(
    "/{user_uuid}",
    response_model=UserResponse,
    summary="Update user profile",
    description="""
    Update user profile information.

    Permissions:
    - Users can update their own profile
    - Admins can update any user's profile

    Updatable fields:
    - first_name: User's first name
    - last_name: User's last name
    - email: Email address (must be unique)

    All fields are optional - only provided fields will be updated.

    Note: Password changes should use a separate dedicated endpoint
    (not implemented in this version).
    """,
)
async def update_user(
    user_uuid: UUID,
    user_data: UserUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    """Update user profile."""
    logger.info(
        f"User update request for user_uuid: {user_uuid}",
        extra={
            "requesting_user_uuid": str(current_user.uuid),
            "target_user_uuid": str(user_uuid),
            "update_fields": user_data.model_dump(exclude_unset=True),
        },
    )

    user_service = UserService(db)

    try:
        updated_user = await user_service.update_user(
            user_uuid=user_uuid, user_data=user_data, requesting_user=current_user
        )

        logger.info(
            "User updated successfully",
            extra={
                "requesting_user_uuid": str(current_user.uuid),
                "updated_user_uuid": str(user_uuid),
                "action": "update_user",
            },
        )

        return updated_user

    except ValueError as e:
        # Determine status code based on error message
        if "not found" in str(e).lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "permission" in str(e).lower():
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        logger.warning(
            f"User update failed: {str(e)}",
            extra={
                "requesting_user_uuid": str(current_user.uuid),
                "target_user_uuid": str(user_uuid),
                "error": str(e),
            },
        )

        raise HTTPException(status_code=status_code, detail=str(e))


@router.delete(
    "/{user_uuid}",
    response_model=MessageResponse,
    summary="Delete user (Admin only)",
    description="""
    Permanently delete a user account from the system.

    Admin access required

    Restrictions:
    - Admins cannot delete their own account
    - This is a permanent operation (hard delete)
    """,
)
async def delete_user(
    user_uuid: UUID,
    admin: AdminUser,
    db: DatabaseSession,
):
    """Delete user (admin only)."""
    logger.warning(
        f"User deletion request for user_uuid: {user_uuid}",
        extra={
            "admin_uuid": str(admin.uuid),
            "target_user_uuid": str(user_uuid),
            "action": "delete_user",
        },
    )

    user_service = UserService(db)

    try:
        await user_service.delete_user(user_uuid=user_uuid, requesting_user=admin)

        logger.warning(
            f"User deleted: {user_uuid}",
            extra={
                "admin_uuid": str(admin.uuid),
                "deleted_user_uuid": str(user_uuid),
                "action": "delete_user_success",
            },
        )

        return MessageResponse(
            message="User deleted successfully",
            detail=f"User with UUID {user_uuid} has been permanently deleted",
        )

    except ValueError as e:
        if "not found" in str(e).lower():
            status_code = status.HTTP_404_NOT_FOUND
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        logger.error(
            f"User deletion failed: {str(e)}",
            extra={
                "admin_uuid": str(admin.uuid),
                "target_user_uuid": str(user_uuid),
                "error": str(e),
            },
        )

        raise HTTPException(status_code=status_code, detail=str(e))
