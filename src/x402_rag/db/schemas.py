"""Database schemas for chunk purchases."""

from datetime import datetime

from sqlalchemy import DateTime, PrimaryKeyConstraint, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class ChunkPurchase(Base):
    """Track which chunks a user has already paid for."""

    __tablename__ = "chunk_purchases"

    user_address: Mapped[str] = mapped_column(String, nullable=False)
    chunk_id: Mapped[str] = mapped_column(String, nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (PrimaryKeyConstraint("user_address", "chunk_id"),)
