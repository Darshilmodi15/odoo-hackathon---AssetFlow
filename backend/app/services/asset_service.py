import uuid
from datetime import datetime, timezone

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.models.asset import Asset
from app.models.organization import AssetCategory, Department
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetUpdate

MANAGE_ASSETS_ROLES = {"admin", "asset_manager"}
VALID_ASSET_STATUSES = {"available", "allocated", "reserved", "under_maintenance", "lost", "retired", "disposed"}


def _next_tag(db: Session) -> str:
    count = db.scalar(select(func.count()).select_from(Asset)) or 0
    # Avoid collisions if demo data was inserted manually.
    for number in range(count + 1, count + 10_000):
        tag = f"AF-{number:04d}"
        if not db.scalar(select(Asset.id).where(Asset.tag == tag)):
            return tag
    raise api_error(status.HTTP_409_CONFLICT, "Unable to generate asset tag", "ASSET_TAG_CONFLICT")


def list_assets(db: Session) -> list[Asset]:
    return list(db.scalars(select(Asset).order_by(Asset.updated_at.desc())).all())


def get_asset(db: Session, asset_id: uuid.UUID) -> Asset:
    asset = db.get(Asset, asset_id)
    if not asset:
        raise api_error(status.HTTP_404_NOT_FOUND, "Asset not found", "ASSET_NOT_FOUND")
    return asset


def create_asset(db: Session, payload: AssetCreate, actor: User) -> Asset:
    if actor.role not in MANAGE_ASSETS_ROLES:
        raise api_error(status.HTTP_403_FORBIDDEN, "Not enough permissions", "FORBIDDEN_ROLE")
    if not db.get(AssetCategory, payload.category_id):
        raise api_error(status.HTTP_404_NOT_FOUND, "Category not found", "CATEGORY_NOT_FOUND")
    if payload.department_id and not db.get(Department, payload.department_id):
        raise api_error(status.HTTP_404_NOT_FOUND, "Department not found", "DEPARTMENT_NOT_FOUND")
    asset = Asset(
        tag=_next_tag(db),
        name=payload.name,
        category_id=payload.category_id,
        serial_number=payload.serial_number,
        department_id=payload.department_id,
        location=payload.location,
        condition=payload.condition,
        status=payload.status,
        shared=payload.shared,
        acquisition_date=payload.acquisition_date,
        acquisition_cost=payload.acquisition_cost,
        notes=payload.notes,
    )
    db.add(asset)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise api_error(status.HTTP_409_CONFLICT, "Asset tag or serial number already exists", "ASSET_ALREADY_EXISTS")
    db.refresh(asset)
    return asset


def update_asset(db: Session, asset_id: uuid.UUID, payload: AssetUpdate, actor: User) -> Asset:
    if actor.role not in MANAGE_ASSETS_ROLES:
        raise api_error(status.HTTP_403_FORBIDDEN, "Not enough permissions", "FORBIDDEN_ROLE")
    asset = get_asset(db, asset_id)
    data = payload.model_dump(exclude_unset=True)
    if "category_id" in data and data["category_id"] and not db.get(AssetCategory, data["category_id"]):
        raise api_error(status.HTTP_404_NOT_FOUND, "Category not found", "CATEGORY_NOT_FOUND")
    if "department_id" in data and data["department_id"] and not db.get(Department, data["department_id"]):
        raise api_error(status.HTTP_404_NOT_FOUND, "Department not found", "DEPARTMENT_NOT_FOUND")
    if "assigned_to_id" in data and data["assigned_to_id"] and not db.get(User, data["assigned_to_id"]):
        raise api_error(status.HTTP_404_NOT_FOUND, "User not found", "USER_NOT_FOUND")
    if "status" in data and data["status"] not in VALID_ASSET_STATUSES:
        raise api_error(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid asset status", "INVALID_STATUS")
    for key, value in data.items():
        setattr(asset, key, value)
    asset.updated_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise api_error(status.HTTP_409_CONFLICT, "Asset serial number already exists", "ASSET_ALREADY_EXISTS")
    db.refresh(asset)
    return asset
