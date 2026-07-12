import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.asset import Asset, Allocation
from app.models.maintenance import MaintenanceRequest, MaintenanceHistory
from app.models.user import User
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate
from app.services.notification import NotificationService
from app.services.log import LogService

class MaintenanceService:
    @staticmethod
    def get_all(db: Session):
        return db.query(MaintenanceRequest).all()

    @staticmethod
    def create(db: Session, maint_in: MaintenanceCreate, actor: User):
        # 1. Get asset
        asset = db.query(Asset).filter(Asset.id == maint_in.asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # 2. Generate maintenance code
        count = db.query(MaintenanceRequest).count()
        code = f"MR-{str(count + 1).zfill(4)}"

        # 3. Create request
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

        # 4. Log initial history
        history = MaintenanceHistory(
            request_id=maint_obj.id,
            status="pending",
            note="Ticket raised",
            by_id=actor.id
        )
        db.add(history)
        db.commit()

        # Log action
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
        return maint_obj

    @staticmethod
    def update_status(db: Session, request_id: uuid.UUID, update_in: MaintenanceUpdate, actor: User):
        # 1. Get request
        maint = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
        if not maint:
            raise HTTPException(status_code=404, detail="Maintenance request not found")

        # 2. Update status and cost
        prev_status = maint.status
        maint.status = update_in.status.lower()

        if update_in.technician_id:
            maint.technician_id = update_in.technician_id
        if update_in.estimated_cost is not None:
            maint.estimated_cost = update_in.estimated_cost
        if update_in.actual_cost is not None:
            maint.actual_cost = update_in.actual_cost
        if update_in.resolution_notes:
            maint.resolution_notes = update_in.resolution_notes

        # 3. Asset status triggers based on workflow transitions
        asset = db.query(Asset).filter(Asset.id == maint.asset_id).first()
        if asset:
            if maint.status == "approved":
                asset.status = "under_maintenance"
            elif maint.status == "resolved":
                # Check if currently assigned to any employee
                if asset.assigned_to_id:
                    asset.status = "allocated"
                else:
                    asset.status = "available"

        # 4. Log state change in history
        history = MaintenanceHistory(
            request_id=maint.id,
            status=maint.status,
            note=update_in.note or f"Status changed from {prev_status} to {maint.status}",
            by_id=actor.id
        )
        db.add(history)
        db.commit()
        db.refresh(maint)

        # Notify requester
        NotificationService.create(
            db=db,
            user_id=maint.requested_by_id,
            notification_type="maintenance",
            title=f"Maintenance {maint.status.capitalize()}",
            message=f"Maintenance request {maint.code} is now {maint.status}.",
            link=f"/maintenance/{maint.id}"
        )

        # Log action
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
