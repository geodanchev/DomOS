"""User settings API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import os
import uuid
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserResponse,
    UserProfileUpdate,
    PasswordChange,
    UsernameChange,
)
from app.api.auth import get_current_user
from app.core.security import verify_password, get_password_hash

router = APIRouter()

# Directory for avatar uploads
AVATAR_UPLOAD_DIR = os.getenv("AVATAR_UPLOAD_DIR", "/app/uploads/avatars")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile information."""
    return UserResponse.model_validate(current_user)


@router.put("/me/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user's profile.
    
    Only provided fields will be updated.
    """
    # Check if email is being changed and already exists
    if profile_data.email is not None:
        existing_email = db.query(User).filter(
            User.email == profile_data.email,
            User.id != current_user.id
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Този email вече се използва от друг потребител",
            )
    
    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.post("/me/password", response_model=dict)
async def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change current user's password.
    
    Requires current password verification.
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Текущата парола е грешна",
        )
    
    # Check that new password is different from current
    if verify_password(password_data.new_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Новата парола трябва да е различна от текущата",
        )
    
    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Паролата е сменена успешно"}


@router.post("/me/username", response_model=UserResponse)
async def change_username(
    username_data: UsernameChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change current user's username.
    
    Requires password verification for security.
    """
    # Verify password
    if not verify_password(username_data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Грешна парола",
        )
    
    # Check if username already exists
    existing_user = db.query(User).filter(
        User.username == username_data.new_username,
        User.id != current_user.id
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Това потребителско име вече е заето",
        )
    
    # Update username
    current_user.username = username_data.new_username
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a new avatar image.
    
    Supported formats: JPEG, PNG, GIF, WebP
    Maximum size: 5MB
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невалиден формат. Позволени са: JPEG, PNG, GIF, WebP",
        )
    
    # Read file content
    content = await file.read()
    
    # Check file size (5MB limit)
    max_size = 5 * 1024 * 1024  # 5MB
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файлът е твърде голям. Максимум 5MB.",
        )
    
    # Create upload directory if it doesn't exist
    os.makedirs(AVATAR_UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"{current_user.id}_{uuid.uuid4().hex}.{file_extension}"
    file_path = os.path.join(AVATAR_UPLOAD_DIR, unique_filename)
    
    # Delete old avatar if exists
    if current_user.avatar_url:
        old_filename = current_user.avatar_url.split("/")[-1]
        old_path = os.path.join(AVATAR_UPLOAD_DIR, old_filename)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass  # Ignore errors when deleting old avatar
    
    # Save new avatar
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Update user avatar URL
    # URL will be served through a static files endpoint
    avatar_url = f"/uploads/avatars/{unique_filename}"
    current_user.avatar_url = avatar_url
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.delete("/me/avatar", response_model=UserResponse)
async def delete_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete current user's avatar."""
    if current_user.avatar_url:
        # Delete avatar file
        filename = current_user.avatar_url.split("/")[-1]
        file_path = os.path.join(AVATAR_UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass  # Ignore errors when deleting
        
        # Clear avatar URL
        current_user.avatar_url = None
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)
