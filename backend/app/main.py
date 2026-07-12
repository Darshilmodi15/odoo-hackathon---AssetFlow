from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db, engine
from app.db.base import Base
# Import models to ensure they are registered with Base.metadata before create_all
from fastapi.responses import JSONResponse
from app.services.booking import BookingOverlapException
import app.models  # noqa
from app.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables for local development/testing convenience
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.project_name,
    description="Enterprise Asset & Resource Management System Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# Set up CORS middleware for development frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(BookingOverlapException)
def booking_overlap_exception_handler(request, exc):
    return JSONResponse(
        status_code=409,
        content={
            "detail": exc.message,
            "suggestions": exc.suggestions
        }
    )

def check_database(db: Session) -> str:
    db.execute(text("SELECT 1"))
    return "connected"

@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """
    Service health check endpoint with PostgreSQL connectivity verification.
    """
    try:
        database_status = check_database(db)
    except SQLAlchemyError:
        return {"status": "error", "database": "disconnected"}

    return {"status": "ok", "database": database_status}

@app.get("/api/health/db-status", tags=["Health"])
def database_health_check(db: Session = Depends(get_db)):
    """
    Dedicated PostgreSQL connectivity check used before API integration work.
    """
    try:
        database_status = check_database(db)
    except SQLAlchemyError:
        return {"status": "error", "database": "disconnected"}

    return {"status": "ok", "database": database_status}

# Include routes under the /api prefix
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
