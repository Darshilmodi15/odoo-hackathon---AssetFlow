"""Asset category service – business logic and database operations."""
import uuid
from typing import Optional

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.core import errors
from app.models.organization import AssetCategory
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryStatusPatch


class CategoryService:
    # ── List ─────────────────────────────────────────────────────────────────

    @staticmethod
    def get_list(
        db: Session,
        *,
        search: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "name",
        order: str = "asc",
    ):
        q = db.query(AssetCategory)

        if search:
            pattern = f"%{search}%"
            q = q.filter(AssetCategory.name.ilike(pattern))
        if status:
            q = q.filter(AssetCategory.status == status)

        sort_col = getattr(AssetCategory, sort_by, AssetCategory.name)
        if order.lower() == "desc":
            sort_col = sort_col.desc()
        q = q.order_by(sort_col)

        total = q.count()
        items = q.offset(skip).limit(limit).all()
        return items, total

    # ── Read one ─────────────────────────────────────────────────────────────

    @staticmethod
    def get_by_id(db: Session, category_id: uuid.UUID) -> AssetCategory:
        cat = db.query(AssetCategory).filter(AssetCategory.id == category_id).first()
        if not cat:
            errors.category_not_found()
        return cat  # type: ignore[return-value]

    # ── Create ────────────────────────────────────────────────────────────────

    @staticmethod
    def create(db: Session, cat_in: CategoryCreate) -> AssetCategory:
        if db.query(AssetCategory).filter(AssetCategory.name == cat_in.name).first():
            errors.category_name_conflict()

        db_obj = AssetCategory(
            name=cat_in.name,
            description=cat_in.description,
            status=cat_in.status or "active",
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # ── Update ────────────────────────────────────────────────────────────────

    @staticmethod
    def update(
        db: Session, category_id: uuid.UUID, cat_in: CategoryUpdate
    ) -> AssetCategory:
        cat = CategoryService.get_by_id(db, category_id)
        update_data = cat_in.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] != cat.name:
            if db.query(AssetCategory).filter(
                AssetCategory.name == update_data["name"]
            ).first():
                errors.category_name_conflict()

        for field, value in update_data.items():
            setattr(cat, field, value)

        db.commit()
        db.refresh(cat)
        return cat

    # ── Status patch ──────────────────────────────────────────────────────────

    @staticmethod
    def patch_status(
        db: Session, category_id: uuid.UUID, patch: CategoryStatusPatch
    ) -> AssetCategory:
        cat = CategoryService.get_by_id(db, category_id)
        cat.status = patch.status
        db.commit()
        db.refresh(cat)
        return cat
