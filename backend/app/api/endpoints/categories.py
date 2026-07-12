import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.category import AssetCategory
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter()

@router.get("", response_model=List[CategoryResponse])
def read_categories(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve asset categories. (All authenticated users can list)
    """
    categories = db.query(AssetCategory).all()
    return categories

@router.post("", response_model=CategoryResponse)
def create_category(
    *,
    db: Session = Depends(deps.get_db),
    category_in: CategoryCreate,
    current_user: User = Depends(deps.check_role(["admin"])),
) -> Any:
    """
    Create new asset category. (Admin only)
    """
    category = db.query(AssetCategory).filter(AssetCategory.name == category_in.name).first()
    if category:
        raise HTTPException(
            status_code=400,
            detail="The category with this name already exists.",
        )
    
    new_cat_id = "c_" + uuid.uuid4().hex[:8]
    db_obj = AssetCategory(
        id=new_cat_id,
        name=category_in.name,
        description=category_in.description,
        status=category_in.status or "active"
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.put("/{id}", response_model=CategoryResponse)
def update_category(
    *,
    db: Session = Depends(deps.get_db),
    id: str,
    category_in: CategoryUpdate,
    current_user: User = Depends(deps.check_role(["admin"])),
) -> Any:
    """
    Update an asset category. (Admin only)
    """
    category = db.query(AssetCategory).filter(AssetCategory.id == id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    update_data = category_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(category, field, update_data[field])
        
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
