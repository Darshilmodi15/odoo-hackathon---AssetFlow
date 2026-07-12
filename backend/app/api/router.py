from fastapi import APIRouter
from app.api.endpoints import (
    auth,
    departments,
    categories,
    employees,
    health,
    assets,
    allocations,
    transfers,
    bookings,
    maintenance,
    audits,
    notifications,
    logs,
    reports,
    inquiries,
)

api_router = APIRouter()

# Authentication & Base endpoints
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(employees.router, prefix="/employees", tags=["Employees"])

# Core Setup and Phase 2, 3, 4 endpoints
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(categories.router, prefix="/categories", tags=["Asset Categories"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(allocations.router, prefix="/allocations", tags=["Allocations"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["Transfers"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance"])
api_router.include_router(audits.router, prefix="/audits", tags=["Audits"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(logs.router, prefix="/activity-logs", tags=["Activity Logs"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(inquiries.router, prefix="/inquiries", tags=["Inquiries"])
