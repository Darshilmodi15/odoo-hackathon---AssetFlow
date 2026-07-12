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
        db.add(n)
        db.commit()
        db.refresh(n)
        return n
