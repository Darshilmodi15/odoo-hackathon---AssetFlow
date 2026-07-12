<<<<<<< HEAD
from fastapi import Depends, FastAPI
=======
from contextlib import asynccontextmanager
from fastapi import FastAPI
>>>>>>> origin/rudra-backend-work
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_session

from app.api.router import api_router
from app.core.database import engine, SessionLocal
from app.models.base import Base
from app.db.seed import seed_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Run database seeder
    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()
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

<<<<<<< HEAD

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

=======
# Include all API routers under the '/api' prefix
app.include_router(api_router, prefix="/api")
>>>>>>> origin/rudra-backend-work

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
