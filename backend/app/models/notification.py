import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, String, Text, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, GUID

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # "allocation", "transfer", "maintenance", "booking", "audit", "overdue"
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    link: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
