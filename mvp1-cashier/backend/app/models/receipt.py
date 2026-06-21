"""Receipt model - разписки/квитанции.

Спринт 3: Разписки с поддръжка на копия и PDF генериране.
"""

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.user import User


class Receipt(Base, TimestampMixin):
    """Разписка за плащане.
    
    Бизнес правила:
    - Едно плащане = една оригинална разписка (is_copy=False)
    - Могат да се създават неограничен брой копия (is_copy=True)
    - Копията имат същия receipt_number като оригинала
    - Копие на копие сочи към оригинала, не към копието
    
    Пример:
        Receipt #2026-000001 (original) -> Payment #1
        Receipt #2026-000001 (copy)     -> original_receipt_id = 1
        Receipt #2026-000001 (copy)     -> original_receipt_id = 1
    """
    
    __tablename__ = "receipts"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Бизнес номер на разписката (формат: YYYY-NNNNNN)
    receipt_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Номер на разписката (YYYY-NNNNNN)"
    )
    
    # Връзка с плащането
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID на плащането"
    )
    
    # Флаг за копие
    is_copy: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Дали е копие (True) или оригинал (False)"
    )
    
    # Референция към оригиналната разписка (само за копия)
    original_receipt_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("receipts.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID на оригиналната разписка (само за копия)"
    )
    
    # Кога е издадена
    issued_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Дата и час на издаване"
    )
    
    # Кой е издал разписката
    issued_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID на потребителя издал разписката"
    )
    
    # Relationships
    payment: Mapped["Payment"] = relationship(back_populates="receipts")
    issued_by: Mapped[Optional["User"]] = relationship(back_populates="issued_receipts")
    original_receipt: Mapped[Optional["Receipt"]] = relationship(
        "Receipt",
        remote_side=[id],
        backref="copies"
    )
    
    def __repr__(self) -> str:
        copy_str = " (COPY)" if self.is_copy else ""
        return f"<Receipt(id={self.id}, number='{self.receipt_number}'{copy_str}, payment_id={self.payment_id})>"
