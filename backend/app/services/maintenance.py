import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.asset import Asset
from app.models.maintenance import MaintenanceRequest, MaintenanceHistory
from app.models.user import User
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate
from app.services.notification import NotificationService
from app.services.log import LogService

MANAGEMENT_ROLES = {"admin", "asset_manager", "department_head"}
TERMINAL_ASSET_STATUSES = {"lost", "retired", "disposed"}
STATUS_ALIASES = {"technician_assigned": "assigned"}
TRANSITIONS = {
    "pending": {"approved", "rejected"},
    "approved": {"assigned"},
    "assigned": {"in_progress"},
    "in_progress": {"resolved"},
    "rejected": set(),
    "resolved": set(),
}


def _normal_status(value: str) -> str:
    value = value.lower()
    return STATUS_ALIASES.get(value, value)


class MaintenanceService:
    @staticmethod
    def get_all(db: Session):
        return db.query(MaintenanceRequest).order_by(MaintenanceRequest.requested_at.desc()).all()

    @staticmethod
    def get_by_id(db: Session, request_id: uuid.UUID):
        maint = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
        if not maint:
            raise HTTPException(status_code=404, detail="Maintenance request not found")
        return maint

    @staticmethod
    def create(db: Session, maint_in: MaintenanceCreate, actor: User):
        asset = db.query(Asset).filter(Asset.id == maint_in.asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        count = db.query(MaintenanceRequest).count()
        code = f"MR-{str(count + 1).zfill(4)}"

        maint_obj = MaintenanceRequest(
            code=code,
            asset_id=maint_in.asset_id,
            requested_by_id=actor.id,
            title=maint_in.title,
            description=maint_in.description,
            priority=maint_in.priority.lower(),
            status="pending",
            preferred_date=maint_in.preferred_date
        )
        db.add(maint_obj)
        db.commit()
        db.refresh(maint_obj)

        history = MaintenanceHistory(
            request_id=maint_obj.id,
            status="pending",
            note="Ticket raised",
            by_id=actor.id
        )
        db.add(history)
        db.commit()

        LogService.create(
            db=db,
            user_id=actor.id,
            action="create_maintenance",
            module="Maintenance",
            description=f"Raised maintenance request {code} for {asset.tag}",
            role=actor.role,
            entity_id=maint_obj.id,
            status="success"
        )
        for manager in db.query(User).filter(User.role.in_(["admin", "asset_manager"]), User.status == "active").all():
            NotificationService.create(
                db=db,
                user_id=manager.id,
                notification_type="maintenance",
                title="Maintenance request raised",
                message=f"{maint_obj.code} was raised for {asset.tag}.",
                link=f"/maintenance/{maint_obj.id}",
            )
        return maint_obj

    @staticmethod
    def update_status(db: Session, request_id: uuid.UUID, update_in: MaintenanceUpdate, actor: User):
        maint = MaintenanceService.get_by_id(db, request_id)
        new_status = _normal_status(update_in.status)
        prev_status = maint.status
        if new_status not in TRANSITIONS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid maintenance status")
        if new_status not in TRANSITIONS.get(prev_status, set()):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot move maintenance request from {prev_status} to {new_status}")
        if new_status in {"approved", "rejected", "assigned"} and actor.role not in MANAGEMENT_ROLES:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        if new_status in {"in_progress", "resolved"} and actor.role not in MANAGEMENT_ROLES and maint.technician_id != actor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        if new_status == "assigned" and not update_in.technician_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="technician_id is required")

        maint.status = new_status

        if update_in.technician_id:
            if not db.query(User).filter(User.id == update_in.technician_id, User.status == "active").first():
                raise HTTPException(status_code=404, detail="Technician not found")
            maint.technician_id = update_in.technician_id
        if update_in.estimated_cost is not None:
            maint.estimated_cost = update_in.estimated_cost
        if update_in.actual_cost is not None:
            maint.actual_cost = update_in.actual_cost
        if update_in.resolution_notes:
            maint.resolution_notes = update_in.resolution_notes

        asset = db.query(Asset).filter(Asset.id == maint.asset_id).first()
        if asset:
            if maint.status == "approved":
                asset.status = "under_maintenance"
            elif maint.status == "resolved":
                if asset.status not in TERMINAL_ASSET_STATUSES:
                    asset.status = "available"
                    asset.assigned_to_id = None

        history = MaintenanceHistory(
            request_id=maint.id,
            status=maint.status,
            note=update_in.note or f"Status changed from {prev_status} to {maint.status}",
            by_id=actor.id
        )
        db.add(history)
        db.commit()
        db.refresh(maint)

        NotificationService.create(
            db=db,
            user_id=maint.requested_by_id,
            notification_type="maintenance",
            title=f"Maintenance {maint.status.capitalize()}",
            message=f"Maintenance request {maint.code} is now {maint.status}.",
            link=f"/maintenance/{maint.id}"
        )
        if maint.technician_id and maint.technician_id != maint.requested_by_id:
            NotificationService.create(
                db=db,
                user_id=maint.technician_id,
                notification_type="maintenance",
                title="Maintenance assigned",
                message=f"You are assigned to {maint.code}.",
                link=f"/maintenance/{maint.id}",
            )

        LogService.create(
            db=db,
            user_id=actor.id,
            action="update_maintenance",
            module="Maintenance",
            description=f"Moved maintenance request {maint.code} to {maint.status}",
            role=actor.role,
            entity_id=maint.id,
            status="success"
        )
        return maint
