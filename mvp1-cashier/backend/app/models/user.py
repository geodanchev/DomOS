"""User model - потребители (касиери)."""

from enum import Enum
from sqlalchemy import String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.payment import Payment


class UserRole(str, Enum):
    """Роля на потребителя."""
    ADMIN = "admin"      # Администратор
    CASHIER = "cashier"  # Касиер (Цецка)
    VIEWER = "viewer"    # Само преглед


class User(Base, TimestampMixin):
    """Потребител на системата.
    
    За MVP 1 - основно касиери като Цецка.
    """
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Потребителско име
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Потребителско име за вход"
    )
    
    # Парола (хеширана)
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Хеширана парола"
    )
    
    # Име за показване
    display_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Име за показване (напр. 'Цецка')"
    )
    
    # Роля
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.CASHIER,
        nullable=False,
        comment="Роля на потребителя"
    )
    
    # Активен ли е
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Дали потребителят е активен"
    )
    
    # Relationships
    collected_payments: Mapped[list["Payment"]] = relationship(
        back_populates="collected_by",
        foreign_keys="Payment.collected_by_id"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role={self.role.value})>"
