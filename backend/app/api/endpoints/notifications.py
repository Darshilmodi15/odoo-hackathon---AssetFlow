from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api import deps
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse

router = APIRouter()

@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    List all notifications for the authenticated user.
    """
    return db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.at.desc()).all()

@router.put("/{id}/read")
def mark_read(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Mark a notification as read.
    """
    n = db.query(Notification).filter(Notification.id == id, Notification.user_id == current_user.id).first()
    if n:
        n.read = True
        db.commit()
    return {"status": "ok"}

@router.post("/mark-all-read")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Mark all notifications for the user as read.
    """
    db.query(Notification).filter(Notification.user_id == current_user.id).update({"read": True})
    db.commit()
    return {"status": "ok"}
