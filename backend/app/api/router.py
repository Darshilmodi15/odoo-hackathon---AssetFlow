from fastapi import APIRouter
from app.api.endpoints import departments, categories

api_router = APIRouter()

api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(categories.router, prefix="/categories", tags=["Asset Categories"])
