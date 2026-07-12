from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.category import CategoryCreate, CategoryResponse
from app.services.category import CategoryService

router = APIRouter()

@router.get("", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """
    Get all asset categories.
    """
    return CategoryService.get_all(db)

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(cat_in: CategoryCreate, db: Session = Depends(get_db)):
    """
    Create a new asset category.
    """
    return CategoryService.create(db, cat_in)
