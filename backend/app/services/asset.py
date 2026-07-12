"""Asset service – business logic and database operations.

  Scope (Rudra):
    - generate_next_tag
    - get_list  (with full filtering)
    - get_by_id
    - create
    - update
    - patch_status

  Allocation / Transfer / Return methods kept for backward-compatibility with
  Darshil's endpoint code – do not remove them.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core import errors as err
from app.models.asset import Asset, Allocation, TransferRequest
from app.models.organization import AssetCategory, Department
from app.models.user import User
from app.schemas.asset import (
    AssetCreate,
    AssetUpdate,
    AssetStatusPatch,
    AllocationCreate,
    AllocationReturn,
    TransferCreate,
    TransferStatusUpdate,
    ASSET_STATUSES,
    PROTECTED_STATUSES,
)
from app.services.notification import NotificationService
from app.services.log import LogService


class AssetService:
    # ── Tag generation ────────────────────────────────────────────────────────

    @staticmethod
    def generate_next_tag(db: Session) -> str:
        assets = db.query(Asset).filter(Asset.tag.like("AF-%")).all()
        if not assets:
            return "AF-0001"
        numbers: list[int] = []
        for a in assets:
            try:
                numbers.append(int(a.tag.split("-")[1]))
            except (IndexError, ValueError):
                continue
        return f"AF-{str(max(numbers, default=0) + 1).zfill(4)}"

    # ── List ──────────────────────────────────────────────────────────────────

    @staticmethod
    def get_list(
        db: Session,
        *,
        search: Optional[str] = None,
        tag: Optional[str] = None,
        serial_number: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        department_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        condition: Optional[str] = None,
        location: Optional[str] = None,
        is_shared: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "name",
        order: str = "asc",
    ):
        q = db.query(Asset)

        if search:
            pattern = f"%{search}%"
            q = q.filter(
                or_(
                    Asset.name.ilike(pattern),
                    Asset.tag.ilike(pattern),
                    Asset.serial_number.ilike(pattern),
                )
            )
        if tag:
            q = q.filter(Asset.tag.ilike(f"%{tag}%"))
        if serial_number:
            q = q.filter(Asset.serial_number.ilike(f"%{serial_number}%"))
        if category_id:
            q = q.filter(Asset.category_id == category_id)
        if department_id:
            q = q.filter(Asset.department_id == department_id)
        if status:
            q = q.filter(Asset.status == status)
        if condition:
            q = q.filter(Asset.condition == condition)
        if location:
            q = q.filter(Asset.location.ilike(f"%{location}%"))
        if is_shared is not None:
            q = q.filter(Asset.shared == is_shared)

        sort_col = getattr(Asset, sort_by, Asset.name)
        if order.lower() == "desc":
            sort_col = sort_col.desc()
        q = q.order_by(sort_col)

        total = q.count()
        items = q.offset(skip).limit(limit).all()
        return items, total

    # ── Read one ──────────────────────────────────────────────────────────────

    @staticmethod
    def get_by_id(db: Session, asset_id: uuid.UUID) -> Asset:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            err.asset_not_found()
        return asset  # type: ignore[return-value]

    # ── Create ────────────────────────────────────────────────────────────────

    @staticmethod
    def create(db: Session, asset_in: AssetCreate, actor: User) -> Asset:
        # Validate category exists
        if not db.query(AssetCategory).filter(
            AssetCategory.id == asset_in.category_id
        ).first():
            err.not_found("Asset category not found", "CATEGORY_NOT_FOUND")

        # Validate department exists when provided
        if asset_in.department_id and not db.query(Department).filter(
            Department.id == asset_in.department_id
        ).first():
            err.not_found("Department not found", "DEPARTMENT_NOT_FOUND")

        # Unique serial check
        if asset_in.serial_number:
            if db.query(Asset).filter(
                Asset.serial_number == asset_in.serial_number
            ).first():
                err.asset_serial_conflict()

        tag = AssetService.generate_next_tag(db)

        db_obj = Asset(
            tag=tag,
            name=asset_in.name.strip(),
            category_id=asset_in.category_id,
            serial_number=asset_in.serial_number or None,
            department_id=asset_in.department_id,
            location=asset_in.location.strip(),
            condition=asset_in.condition,
            status="available",
            shared=asset_in.shared or False,
            acquisition_date=asset_in.acquisition_date,
            acquisition_cost=asset_in.acquisition_cost or 0.0,
            notes=asset_in.notes or None,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        LogService.create(
            db=db,
            user_id=actor.id,
            action="create_asset",
            module="Assets",
            description=f"Registered asset {db_obj.name} with tag {db_obj.tag}",
            role=actor.role,
            entity_id=db_obj.id,
            status="success",
        )
        return db_obj

    # ── Update ────────────────────────────────────────────────────────────────

    @staticmethod
    def update(
        db: Session, asset_id: uuid.UUID, asset_in: AssetUpdate, actor: User
    ) -> Asset:
        asset = AssetService.get_by_id(db, asset_id)
        update_data = asset_in.model_dump(exclude_unset=True)

        # category must exist
        if "category_id" in update_data:
            if not db.query(AssetCategory).filter(
                AssetCategory.id == update_data["category_id"]
            ).first():
                err.not_found("Asset category not found", "CATEGORY_NOT_FOUND")

        # department must exist when provided
        if "department_id" in update_data and update_data["department_id"]:
            if not db.query(Department).filter(
                Department.id == update_data["department_id"]
            ).first():
                err.not_found("Department not found", "DEPARTMENT_NOT_FOUND")

        # unique serial check
        if "serial_number" in update_data:
            sn = update_data["serial_number"]
            if sn and sn != asset.serial_number:
                if db.query(Asset).filter(Asset.serial_number == sn).first():
                    err.asset_serial_conflict()
            # If empty string, store as None
            if sn == "":
                update_data["serial_number"] = None

        # Guard: do NOT allow moving OUT of a protected status through generic update
        # (allocation / maintenance etc. must use their own workflow endpoints)
        # We only block transitions FROM protected TO something else here.
        if "status" in update_data:
            new_status = update_data["status"]
            if new_status not in ASSET_STATUSES:
                err.invalid_asset_status(new_status)
            if asset.status in PROTECTED_STATUSES and new_status not in PROTECTED_STATUSES:
                err.bad_request(
                    f"Cannot change status from '{asset.status}' via generic update. "
                    "Use the dedicated workflow endpoint.",
                    "PROTECTED_STATUS_TRANSITION",
                )

        for field, value in update_data.items():
            setattr(asset, field, value)

        db.commit()
        db.refresh(asset)

        LogService.create(
            db=db,
            user_id=actor.id,
            action="update_asset",
            module="Assets",
            description=f"Updated asset {asset.tag} ({asset.name})",
            role=actor.role,
            entity_id=asset.id,
            status="success",
        )
        return asset

    # ── Status patch ──────────────────────────────────────────────────────────

    @staticmethod
    def patch_status(
        db: Session, asset_id: uuid.UUID, patch: AssetStatusPatch, actor: User
    ) -> Asset:
        asset = AssetService.get_by_id(db, asset_id)

        # Prevent unsafe transitions when allocation infrastructure is absent
        if asset.status == "allocated" and patch.status == "available":
            # Extension point: once Darshil's allocation module is merged, check
            # for an active Allocation record before permitting this transition.
            active_alloc = db.query(Allocation).filter(
                Allocation.asset_id == asset_id,
                Allocation.status == "active",
            ).first()
            if active_alloc:
                err.bad_request(
                    "Asset has an active allocation. Return the asset via the "
                    "allocation endpoint before marking it available.",
                    "ACTIVE_ALLOCATION_EXISTS",
                )

        asset.status = patch.status
        db.commit()
        db.refresh(asset)

        LogService.create(
            db=db,
            user_id=actor.id,
            action="patch_asset_status",
            module="Assets",
            description=f"Changed status of {asset.tag} to {patch.status}",
            role=actor.role,
            entity_id=asset.id,
            status="success",
        )
        return asset

    # ── Allocation (Darshil's area – kept for backward-compat) ────────────────

    @staticmethod
    def get_all(db: Session):
        return db.query(Asset).all()

    @staticmethod
    def allocate(db: Session, alloc_in: AllocationCreate, actor: User):
        asset = db.query(Asset).filter(Asset.id == alloc_in.asset_id).first()
        if not asset:
            err.asset_not_found()

        if asset.status != "available":
            from fastapi import HTTPException, status as http_status
            if asset.status == "allocated" and asset.assigned_to_id:
                holder = db.query(User).filter(User.id == asset.assigned_to_id).first()
                holder_name = holder.name if holder else "an employee"
                raise HTTPException(
                    status_code=http_status.HTTP_409_CONFLICT,
                    detail=f"Asset is currently allocated to {holder_name}.",
                )
            else:
                raise HTTPException(
                    status_code=http_status.HTTP_409_CONFLICT,
                    detail=f"Asset is currently {asset.status} and cannot be allocated.",
                )

        employee = db.query(User).filter(User.id == alloc_in.employee_id).first()
        if not employee:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Target employee not found")

        asset.status = "allocated"
        asset.assigned_to_id = employee.id
        asset.department_id = employee.department_id or asset.department_id

        alloc_obj = Allocation(
            asset_id=alloc_in.asset_id,
            employee_id=alloc_in.employee_id,
            department_id=employee.department_id,
            expected_return_at=alloc_in.expected_return_at,
            status="active",
            notes=alloc_in.notes,
        )
        db.add(alloc_obj)
        db.commit()
        db.refresh(alloc_obj)

        NotificationService.create(
            db=db,
            user_id=employee.id,
            notification_type="allocation",
            title="Asset Allocated",
            message=f"You have been allocated {asset.name} ({asset.tag}).",
            link=f"/assets/{asset.id}",
        )
        LogService.create(
            db=db,
            user_id=actor.id,
            action="allocate_asset",
            module="Allocations",
            description=f"Allocated asset {asset.tag} to {employee.name}",
            role=actor.role,
            entity_id=alloc_obj.id,
            status="success",
        )
        return alloc_obj

    @staticmethod
    def return_asset(
        db: Session, allocation_id: uuid.UUID, return_in: AllocationReturn, actor: User
    ):
        from fastapi import HTTPException
        alloc = db.query(Allocation).filter(
            Allocation.id == allocation_id,
            Allocation.status == "active",
        ).first()
        if not alloc:
            raise HTTPException(status_code=404, detail="Active allocation record not found")

        alloc.returned_at = datetime.utcnow()
        alloc.return_condition = return_in.return_condition
        alloc.return_notes = return_in.return_notes
        alloc.status = "returned"

        asset = db.query(Asset).filter(Asset.id == alloc.asset_id).first()
        if asset and asset.status not in ["lost", "retired", "disposed"]:
            asset.status = "available"
            asset.assigned_to_id = None
            asset.condition = return_in.return_condition

        db.commit()
        db.refresh(alloc)

        LogService.create(
            db=db,
            user_id=actor.id,
            action="return_asset",
            module="Allocations",
            description=f"Returned asset {asset.tag if asset else ''}",
            role=actor.role,
            entity_id=alloc.id,
            status="success",
        )
        return alloc

    @staticmethod
    def get_transfers(db: Session):
        return db.query(TransferRequest).all()

    @staticmethod
    def create_transfer(db: Session, transfer_in: TransferCreate, actor: User):
        from fastapi import HTTPException, status as http_status
        asset = db.query(Asset).filter(Asset.id == transfer_in.asset_id).first()
        if not asset:
            err.asset_not_found()

        if asset.status != "allocated" or not asset.assigned_to_id:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Asset must be currently allocated to perform a transfer request.",
            )

        to_emp = db.query(User).filter(User.id == transfer_in.to_employee_id).first()
        if not to_emp:
            raise HTTPException(status_code=404, detail="Target employee not found")

        count = db.query(TransferRequest).count()
        code = f"TR-{str(count + 1).zfill(4)}"

        tr_obj = TransferRequest(
            code=code,
            asset_id=transfer_in.asset_id,
            from_employee_id=asset.assigned_to_id,
            to_employee_id=transfer_in.to_employee_id,
            reason=transfer_in.reason,
            requested_by_id=actor.id,
            status="requested",
        )
        db.add(tr_obj)
        db.commit()
        db.refresh(tr_obj)

        LogService.create(
            db=db,
            user_id=actor.id,
            action="create_transfer",
            module="Transfers",
            description=f"Requested transfer of {asset.tag} to {to_emp.name}",
            role=actor.role,
            entity_id=tr_obj.id,
            status="success",
        )
        return tr_obj

    @staticmethod
    def update_transfer_status(
        db: Session,
        transfer_id: uuid.UUID,
        status_in: TransferStatusUpdate,
        actor: User,
    ):
        from fastapi import HTTPException
        tr = db.query(TransferRequest).filter(
            TransferRequest.id == transfer_id,
            TransferRequest.status == "requested",
        ).first()
        if not tr:
            raise HTTPException(status_code=404, detail="Pending transfer request not found")

        tr.approver_id = actor.id
        tr.status = status_in.status.lower()
        asset = db.query(Asset).filter(Asset.id == tr.asset_id).first()

        if tr.status == "approved":
            active_alloc = db.query(Allocation).filter(
                Allocation.asset_id == tr.asset_id,
                Allocation.employee_id == tr.from_employee_id,
                Allocation.status == "active",
            ).first()
            if active_alloc:
                active_alloc.returned_at = datetime.utcnow()
                active_alloc.status = "returned"
                active_alloc.return_condition = asset.condition if asset else "good"
                active_alloc.return_notes = "Closed via approved transfer request"

            to_emp = db.query(User).filter(User.id == tr.to_employee_id).first()
            if asset and to_emp:
                asset.assigned_to_id = to_emp.id
                asset.department_id = to_emp.department_id or asset.department_id
                asset.status = "allocated"

            new_alloc = Allocation(
                asset_id=tr.asset_id,
                employee_id=tr.to_employee_id,
                department_id=to_emp.department_id if to_emp else None,
                status="active",
                notes=f"Created via transfer {tr.code}",
            )
            db.add(new_alloc)

            if to_emp:
                NotificationService.create(
                    db=db,
                    user_id=tr.to_employee_id,
                    notification_type="transfer",
                    title="Asset Transferred",
                    message=f"Asset {asset.name if asset else ''} has been transferred to you.",
                    link=f"/assets/{tr.asset_id}",
                )
            tr.status = "completed"

        elif tr.status == "rejected":
            NotificationService.create(
                db=db,
                user_id=tr.requested_by_id,
                notification_type="transfer",
                title="Transfer Rejected",
                message=f"Your transfer request {tr.code} was rejected.",
                link=f"/assets/{tr.asset_id}",
            )

        db.commit()
        db.refresh(tr)

        LogService.create(
            db=db,
            user_id=actor.id,
            action="update_transfer",
            module="Transfers",
            description=f"Updated transfer {tr.code} to {tr.status}",
            role=actor.role,
            entity_id=tr.id,
            status="success",
        )
        return tr
