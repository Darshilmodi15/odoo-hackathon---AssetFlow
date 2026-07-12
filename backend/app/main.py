from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.routes import allocations, assets, auth, bookings, organization, transfers, users
from app.core.config import settings
from app.db.session import get_session

app = FastAPI(
    title=settings.project_name,
    description="Enterprise Asset & Resource Management System Backend",
    version="1.0.0",
)

# Set up CORS middleware for development frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        settings.frontend_origin,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_v1_str)
app.include_router(users.router, prefix=settings.api_v1_str)
app.include_router(organization.router, prefix=settings.api_v1_str)
app.include_router(assets.router, prefix=settings.api_v1_str)
app.include_router(allocations.router, prefix=settings.api_v1_str)
app.include_router(transfers.router, prefix=settings.api_v1_str)
app.include_router(bookings.router, prefix=settings.api_v1_str)


def check_database(db: Session) -> str:
    db.execute(text("SELECT 1"))
    return "connected"


@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_session)):
    """
    Service health check endpoint with PostgreSQL connectivity verification.
    """
    try:
        database_status = check_database(db)
    except SQLAlchemyError:
        return {"status": "error", "database": "disconnected"}

    return {"status": "ok", "database": database_status}


@app.get("/api/health/db-status", tags=["Health"])
def database_health_check(db: Session = Depends(get_session)):
    """
    Dedicated PostgreSQL connectivity check used before API integration work.
    """
    try:
        database_status = check_database(db)
    except SQLAlchemyError:
        return {"status": "error", "database": "disconnected"}

    return {"status": "ok", "database": database_status}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
