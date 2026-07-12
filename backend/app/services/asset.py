import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from app.models.asset import Asset, Allocation, TransferRequest
from app.models.user import User
from app.schemas.asset import AssetCreate, AllocationCreate, AllocationReturn, TransferCreate, TransferStatusUpdate
from app.services.notification import NotificationService
from app.services.log import LogService

class AssetService:
    @staticmethod
    def generate_next_tag(db: Session) -> str:
        assets = db.query(Asset).filter(Asset.tag.like("AF-%")).all()
        if not assets:
            return "AF-0001"
        numbers = []
        for a in assets:
            try:
                num = int(a.tag.split("-")[1])
                numbers.append(num)
            except (IndexError, ValueError):
                continue
        max_num = max(numbers) if numbers else 0
        return f"AF-{str(max_num + 1).zfill(4)}"

    @staticmethod
    def get_all(db: Session):
        return db.query(Asset).all()

    @staticmethod
    def get_by_id(db: Session, asset_id: uuid.UUID):
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        return asset

    @staticmethod
    def create(db: Session, asset_in: AssetCreate, actor: User):
        # 1. Check duplicate serial number
        duplicate = db.query(Asset).filter(Asset.serial_number == asset_in.serial_number).first()
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Asset with this serial number already exists."
            )

        tag = AssetService.generate_next_tag(db)
        db_obj = Asset(
            tag=tag,
            name=asset_in.name,
            category_id=asset_in.category_id,
            serial_number=asset_in.serial_number,
            department_id=asset_in.department_id,
            location=asset_in.location,
            condition=asset_in.condition,
            status="available",
            shared=asset_in.shared or False,
            acquisition_date=asset_in.acquisition_date,
            acquisition_cost=asset_in.acquisition_cost or 0.0,
            notes=asset_in.notes
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # Log action
        LogService.create(
            db=db,
            user_id=actor.id,
            action="create_asset",
            module="Assets",
            description=f"Registered asset {db_obj.name} with tag {db_obj.tag}",
            role=actor.role,
            entity_id=db_obj.id,
            status="success"
        )
        return db_obj

    @staticmethod
    def allocate(db: Session, alloc_in: AllocationCreate, actor: User):
        # 1. Get asset
        asset = db.query(Asset).filter(Asset.id == alloc_in.asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
            
        # 2. Check if already allocated
        if asset.status != "available":
            if asset.status == "allocated" and asset.assigned_to_id:
                holder = db.query(User).filter(User.id == asset.assigned_to_id).first()
                holder_name = holder.name if holder else "an employee"
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Asset is currently allocated to {holder_name}."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Asset is currently {asset.status} and cannot be allocated."
                )

        # 3. Check target employee
        employee = db.query(User).filter(User.id == alloc_in.employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Target employee not found")

        # 4. Perform allocation
        asset.status = "allocated"
        asset.assigned_to_id = employee.id
        # Associate with employee's department if none specified
        asset.department_id = employee.department_id or asset.department_id
        
        alloc_obj = Allocation(
            asset_id=alloc_in.asset_id,
            employee_id=alloc_in.employee_id,
            department_id=employee.department_id,
            expected_return_at=alloc_in.expected_return_at,
            status="active",
            notes=alloc_in.notes
        )
        db.add(alloc_obj)
        db.commit()
        db.refresh(alloc_obj)

        # Notify employee
        NotificationService.create(
            db=db,
            user_id=employee.id,
            notification_type="allocation",
            title="Asset Allocated",
            message=f"You have been allocated {asset.name} ({asset.tag}).",
            link=f"/assets/{asset.id}"
        )

        # Log action
        LogService.create(
            db=db,
            user_id=actor.id,
            action="allocate_asset",
            module="Allocations",
            description=f"Allocated asset {asset.tag} to {employee.name}",
            role=actor.role,
            entity_id=alloc_obj.id,
            status="success"
        )
        return alloc_obj

    @staticmethod
    def return_asset(db: Session, allocation_id: uuid.UUID, return_in: AllocationReturn, actor: User):
        # 1. Get active allocation
        alloc = db.query(Allocation).filter(
            Allocation.id == allocation_id,
            Allocation.status == "active"
        ).first()
        if not alloc:
            raise HTTPException(status_code=404, detail="Active allocation record not found")

        # 2. Update allocation
        alloc.returned_at = datetime.utcnow()
        alloc.return_condition = return_in.return_condition
        alloc.return_notes = return_in.return_notes
        alloc.status = "returned"

        # 3. Update asset status if not in a decommissioned state
        asset = db.query(Asset).filter(Asset.id == alloc.asset_id).first()
        if asset:
            if asset.status not in ["lost", "retired", "disposed"]:
                asset.status = "available"
                asset.assigned_to_id = None
                asset.condition = return_in.return_condition

        db.commit()
        db.refresh(alloc)

        # Log action
        LogService.create(
            db=db,
            user_id=actor.id,
            action="return_asset",
            module="Allocations",
            description=f"Returned asset {asset.tag if asset else ''}",
            role=actor.role,
            entity_id=alloc.id,
            status="success"
        )
        return alloc

    @staticmethod
    def get_transfers(db: Session):
        return db.query(TransferRequest).all()

    @staticmethod
    def create_transfer(db: Session, transfer_in: TransferCreate, actor: User):
        # 1. Get asset
        asset = db.query(Asset).filter(Asset.id == transfer_in.asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # 2. Check if currently allocated
        if asset.status != "allocated" or not asset.assigned_to_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Asset must be currently allocated to perform a transfer request."
            )

        # 3. Check target employee
        to_emp = db.query(User).filter(User.id == transfer_in.to_employee_id).first()
        if not to_emp:
            raise HTTPException(status_code=404, detail="Target employee not found")

        # 4. Generate transfer code
        count = db.query(TransferRequest).count()
        code = f"TR-{str(count + 1).zfill(4)}"

        tr_obj = TransferRequest(
            code=code,
            asset_id=transfer_in.asset_id,
            from_employee_id=asset.assigned_to_id,
            to_employee_id=transfer_in.to_employee_id,
            reason=transfer_in.reason,
            requested_by_id=actor.id,
            status="requested"
        )
        db.add(tr_obj)
        db.commit()
        db.refresh(tr_obj)

        # Log action
        LogService.create(
            db=db,
            user_id=actor.id,
            action="create_transfer",
            module="Transfers",
            description=f"Requested transfer of {asset.tag} to {to_emp.name}",
            role=actor.role,
            entity_id=tr_obj.id,
            status="success"
        )
        return tr_obj

    @staticmethod
    def update_transfer_status(db: Session, transfer_id: uuid.UUID, status_in: TransferStatusUpdate, actor: User):
        # 1. Get transfer request
        tr = db.query(TransferRequest).filter(
            TransferRequest.id == transfer_id,
            TransferRequest.status == "requested"
        ).first()
        if not tr:
            raise HTTPException(status_code=404, detail="Pending transfer request not found")

        tr.approver_id = actor.id
        tr.status = status_in.status.lower()

        # Get asset
        asset = db.query(Asset).filter(Asset.id == tr.asset_id).first()

        if tr.status == "approved":
            # 1. Close current active allocation
            active_alloc = db.query(Allocation).filter(
                Allocation.asset_id == tr.asset_id,
                Allocation.employee_id == tr.from_employee_id,
                Allocation.status == "active"
            ).first()
            if active_alloc:
                active_alloc.returned_at = datetime.utcnow()
                active_alloc.status = "returned"
                active_alloc.return_condition = asset.condition if asset else "good"
                active_alloc.return_notes = "Closed via approved transfer request"

            # 2. Re-assign asset
            to_emp = db.query(User).filter(User.id == tr.to_employee_id).first()
            if asset and to_emp:
                asset.assigned_to_id = to_emp.id
                asset.department_id = to_emp.department_id or asset.department_id
                asset.status = "allocated"

            # 3. Open new allocation
            new_alloc = Allocation(
                asset_id=tr.asset_id,
                employee_id=tr.to_employee_id,
                department_id=to_emp.department_id if to_emp else None,
                status="active",
                notes=f"Created via transfer {tr.code}"
            )
            db.add(new_alloc)

            # Notify target employee
            NotificationService.create(
                db=db,
                user_id=tr.to_employee_id,
                notification_type="transfer",
                title="Asset Transferred",
                message=f"Asset {asset.name if asset else ''} has been transferred to you.",
                link=f"/assets/{tr.asset_id}"
            )
            
            tr.status = "completed"

        elif tr.status == "rejected":
            # Notify requester
            NotificationService.create(
                db=db,
                user_id=tr.requested_by_id,
                notification_type="transfer",
                title="Transfer Rejected",
                message=f"Your transfer request {tr.code} was rejected.",
                link=f"/assets/{tr.asset_id}"
            )

        db.commit()
        db.refresh(tr)

        # Log action
        LogService.create(
            db=db,
            user_id=actor.id,
            action="update_transfer",
            module="Transfers",
            description=f"Updated transfer {tr.code} to {tr.status}",
            role=actor.role,
            entity_id=tr.id,
            status="success"
        )
        return tr
