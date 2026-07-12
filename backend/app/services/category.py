from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.organization import AssetCategory
from app.schemas.category import CategoryCreate

class CategoryService:
    @staticmethod
    def get_all(db: Session):
        return db.query(AssetCategory).all()

    @staticmethod
    def create(db: Session, cat_in: CategoryCreate):
        # 1. Check duplicate name
        duplicate = db.query(AssetCategory).filter(
            AssetCategory.name == cat_in.name
        ).first()
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Asset Category with this name already exists."
            )

        db_obj = AssetCategory(
            name=cat_in.name,
            description=cat_in.description,
            status=cat_in.status or "active"
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
