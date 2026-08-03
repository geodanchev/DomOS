"""User schemas."""

from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional
import re

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
    email: Optional[str] = Field(None, description="Email адрес")
    phone: Optional[str] = Field(None, max_length=20, description="Телефонен номер")


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
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


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile.
    
    All fields are optional - only provided fields will be updated.
    """
    display_name: Optional[str] = Field(None, min_length=1, max_length=200, description="Име за показване")
    email: Optional[str] = Field(None, description="Email адрес")
    phone: Optional[str] = Field(None, max_length=20, description="Телефонен номер")
    avatar_url: Optional[str] = Field(None, max_length=500, description="URL към профилна снимка")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format if provided."""
        if v is None or v == '':
            return None
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Невалиден email адрес')
        return v.lower()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone format if provided."""
        if v is None or v == '':
            return None
        # Remove spaces and dashes for validation
        cleaned = re.sub(r'[\s\-]', '', v)
        # Allow + at start, then digits only
        if not re.match(r'^\+?[0-9]{6,15}$', cleaned):
            raise ValueError('Невалиден телефонен номер')
        return v


class PasswordChange(BaseModel):
    """Schema for changing password."""
    current_password: str = Field(..., description="Текуща парола")
    new_password: str = Field(..., min_length=4, description="Нова парола")
    confirm_password: str = Field(..., description="Потвърждение на новата парола")
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate that new_password and confirm_password match."""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Паролите не съвпадат')
        return v


class UsernameChange(BaseModel):
    """Schema for changing username."""
    new_username: str = Field(..., min_length=3, max_length=100, description="Ново потребителско име")
    password: str = Field(..., description="Текуща парола за потвърждение")
