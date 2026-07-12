from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    head_id = Column(String, ForeignKey("users.id", name="fk_department_head", use_alter=True), nullable=True)
    parent_id = Column(String, ForeignKey("departments.id", name="fk_department_parent"), nullable=True)
    status = Column(String, default="active", nullable=False)  # "active" or "inactive"

    # Self-referencing parent department
    parent = relationship("Department", remote_side=[id], backref="sub_departments")
    
    # Department Head relationship
    head = relationship("User", foreign_keys=[head_id], post_update=True)
