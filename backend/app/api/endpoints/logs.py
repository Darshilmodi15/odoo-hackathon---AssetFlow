from typing import List
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api import deps
from app.models.user import User
from app.models.log import ActivityLog
from app.schemas.log import LogResponse

router = APIRouter()

@router.get("", response_model=List[LogResponse])
def get_activity_logs(
    module: str | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    List all system activity logs.
    """
    q = db.query(ActivityLog)
    if module:
        q = q.filter(ActivityLog.module == module)
    if user_id:
        q = q.filter(ActivityLog.user_id == user_id)
    if action:
        q = q.filter(ActivityLog.action == action)
    if date_from:
        q = q.filter(ActivityLog.at >= date_from)
    if date_to:
        q = q.filter(ActivityLog.at <= date_to)
    return q.order_by(ActivityLog.at.desc()).all()
