from typing import List
import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_session
from app.models.user import User
from app.models.organization import AssetCategory
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services.category import CategoryService

router = APIRouter()

@router.get("", response_model=List[CategoryResponse])
def read_categories(
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Retrieve asset categories.
    """
    return CategoryService.get_all(db)

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.check_role(["admin", "asset_manager"])),
):
    """
    Create new asset category.
    """
    return CategoryService.create(db, category_in)

@router.put("/{id}", response_model=CategoryResponse)
def update_category(
    id: uuid.UUID,
    category_in: CategoryUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.check_role(["admin", "asset_manager"])),
):
    """
    Update an asset category.
    """
    category = db.query(AssetCategory).filter(AssetCategory.id == id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    update_data = category_in.model_dump(exclude_unset=True)
    
    if "name" in update_data and update_data["name"] != category.name:
        duplicate = db.query(AssetCategory).filter(AssetCategory.name == update_data["name"]).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Asset Category with this name already exists.")

    for field in update_data:
        setattr(category, field, update_data[field])
        
    db.commit()
    db.refresh(category)
    return category
