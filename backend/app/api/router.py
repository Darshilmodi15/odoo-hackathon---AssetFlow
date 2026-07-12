from fastapi import APIRouter
from app.api.endpoints import auth, departments, categories, employees, health

api_router = APIRouter()

# Mount sub-routers
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(departments.router, prefix="/departments")
api_router.include_router(categories.router, prefix="/categories")
api_router.include_router(employees.router, prefix="/employees")
