from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.log import ActivityLog

class LogService:
    @staticmethod
    def create(db: Session, user_id, action, module, description, role, entity_id=None, status=None):
        log = ActivityLog(
            user_id=user_id,
            action=action,
            module=module,
            description=description,
            role=role,
            entity_id=entity_id,
            status=status
        )
        try:
            db.add(log)
            db.commit()
            db.refresh(log)
            return log
        except SQLAlchemyError:
            # Activity logging must not make the primary demo workflow fail on
            # partially migrated demo databases.
            db.rollback()
            return None
