"""User model for authentication and authorization."""
from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, String, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, SoftDeleteMixin


class UserRole(str, Enum):
    """User roles in the system."""
    SUPERADMIN = "superadmin"  # Platform administrator
    BUILDING_MANAGER = "building_manager"  # Домоуправител
    OWNER = "owner"  # Собственик
    RESIDENT = "resident"  # Живущ (not owner)
    VIEWER = "viewer"  # Read-only access


class User(Base, TimestampMixin, SoftDeleteMixin):
    """User account for authentication and authorization.
    
    This represents a system user who can log in.
    A User can have different roles in different buildings.
    """
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="Unique email address for login"
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether user account is active"
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether email is verified"
    )
    
    # Profile
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="User's first name"
    )
    
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="User's last name"
    )
    
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Contact phone number"
    )
    
    # Global role (for platform admins)
    global_role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.RESIDENT,
        nullable=False,
        comment="Global role in the platform"
    )
    
    # Metadata
    last_login: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="Last successful login timestamp"
    )
    
    # Relationships (to be added)
    # residencies: Mapped[list["Residency"]] = relationship(back_populates="user")
    # ownerships: Mapped[list["Ownership"]] = relationship(back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.full_name}')>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_superadmin(self) -> bool:
        """Check if user is platform superadmin."""
        return self.global_role == UserRole.SUPERADMIN
