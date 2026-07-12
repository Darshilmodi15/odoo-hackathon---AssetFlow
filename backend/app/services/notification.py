from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.notification import Notification

class NotificationService:
    @staticmethod
    def create(db: Session, user_id, notification_type, title, message, link=None):
        n = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            link=link
        )
        try:
            db.add(n)
            db.commit()
            db.refresh(n)
            return n
        except SQLAlchemyError:
            # Notifications are demo-supporting, not workflow-critical. Some
            # legacy demo databases do not have this table migrated yet; avoid
            # breaking allocation/transfer/booking flows.
            db.rollback()
            return None
