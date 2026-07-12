from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="employee", nullable=False)  # "admin", "asset_manager", "department_head", "employee"
    department_id = Column(String, ForeignKey("departments.id", name="fk_user_department"), nullable=True)
    status = Column(String, default="active", nullable=False)  # "active" or "inactive"
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship to Department
    department = relationship("Department", foreign_keys=[department_id], backref="employees")
