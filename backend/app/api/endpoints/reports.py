from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.api import deps
from app.models.user import User
from app.models.asset import Asset

router = APIRouter()

@router.get("/dashboard")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get dashboard metrics including count of assets by status.
    """
    stats = db.query(Asset.status, func.count(Asset.id)).group_by(Asset.status).all()
    by_status = {status: count for status, count in stats}
    
    # Ensure standard status keys exist in response
    for s in ["available", "allocated", "reserved", "under_maintenance", "lost", "retired", "disposed"]:
        if s not in by_status:
            by_status[s] = 0
            
    return {"byStatus": by_status}
