from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api import deps
from app.db.session import db_type

router = APIRouter()

@router.get("/health", tags=["Health"])
def health_check(db: Session = Depends(deps.get_db)):
    """
    Check the service health and connection to the database.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = f"connected ({db_type})"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    status_code = "healthy" if db_status.startswith("connected") else "unhealthy"
    
    return {
        "status": status_code,
        "database": db_status
    }
