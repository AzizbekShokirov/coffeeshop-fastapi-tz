"""
User Pydantic schemas for request/response validation.

This module defines all schemas used for:
- User registration and updates
- Authentication (login, tokens)
- User responses
- Verification
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.user import UserRole

# ============================================================================
# Authentication Schemas
# ============================================================================


class UserSignup(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=72, description="User password (8-72 characters)")
    first_name: Optional[str] = Field(None, max_length=100, description="User first name")
    last_name: Optional[str] = Field(None, max_length=100, description="User last name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "first_name": "John",
                "last_name": "Doe",
            }
        }
    )


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., max_length=72, description="User password")

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "user@example.com", "password": "securepassword123"}}
    )


class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    )


class TokenRefresh(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh token")


class VerificationRequest(BaseModel):
    verification_code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")

    model_config = ConfigDict(json_schema_extra={"example": {"verification_code": "123456"}})


# ============================================================================
# User Schemas
# ============================================================================


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100, description="User first name")
    last_name: Optional[str] = Field(None, max_length=100, description="User last name")
    email: Optional[EmailStr] = Field(None, description="User email address")

    model_config = ConfigDict(json_schema_extra={"example": {"first_name": "Jane", "last_name": "Smith"}})


class UserResponse(BaseModel):
    uuid: UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "user",
                "is_verified": True,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        },
    )


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(json_schema_extra={"example": {"users": [], "total": 100, "page": 1, "page_size": 10}})


# ============================================================================
# Message Schemas
# ============================================================================


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Operation successful", "detail": "Additional information"}}
    )
