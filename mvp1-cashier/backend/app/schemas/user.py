"""User schemas."""

from pydantic import BaseModel, Field
from datetime import datetime

from app.models.user import UserRole
from app.schemas.permissions import UIPermissions


class UserBase(BaseModel):
    """Base user fields."""
    username: str = Field(..., min_length=3, max_length=100, description="Потребителско име")
    display_name: str = Field(..., min_length=1, max_length=200, description="Име за показване")
    role: UserRole = Field(UserRole.CASHIER, description="Роля")


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=4, description="Парола")


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str = Field(..., description="Потребителско име")
    password: str = Field(..., description="Парола")


class Token(BaseModel):
    """Schema for JWT token response.
    
    Includes UI permissions for frontend to conditionally render elements.
    Note: Permissions are for UI convenience only - backend always validates.
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    permissions: UIPermissions
