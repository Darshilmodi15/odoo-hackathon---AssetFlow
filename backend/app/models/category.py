from sqlalchemy import Column, String
from app.models.base import Base

class AssetCategory(Base):
    __tablename__ = "asset_categories"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)  # "active" or "inactive"
