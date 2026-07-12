from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api import deps
from app.models.user import User
from app.models.log import ActivityLog
from app.schemas.log import LogResponse

router = APIRouter()

@router.get("", response_model=List[LogResponse])
def get_activity_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    List all system activity logs.
    """
    return db.query(ActivityLog).order_by(ActivityLog.at.desc()).all()
