import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.asset import Asset
from app.models.audit import AuditCycle, AuditAssignment, AuditFinding
from app.models.user import User
from app.schemas.audit import AssignmentCreate, AuditCreate, FindingCreate, FindingUpdate
from app.services.notification import NotificationService
from app.services.log import LogService

MANAGE_AUDIT_ROLES = {"admin", "asset_manager"}
FINDING_STATUSES = {"pending", "verified", "missing", "damaged"}


class AuditService:
    @staticmethod
    def get_all(db: Session):
        return db.query(AuditCycle).all()

    @staticmethod
    def get_by_id(db: Session, cycle_id: uuid.UUID):
        cycle = db.query(AuditCycle).filter(AuditCycle.id == cycle_id).first()
        if not cycle:
            raise HTTPException(status_code=404, detail="Audit cycle not found")
        return cycle

    @staticmethod
    def create(db: Session, audit_in: AuditCreate, actor: User):
        if actor.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create audit cycles")
        cycle = AuditCycle(
            title=audit_in.title,
            scope_department_id=audit_in.scope_department_id,
            scope_location=audit_in.scope_location,
            start_date=audit_in.start_date,
            end_date=audit_in.end_date,
            status="active"
        )
        db.add(cycle)
        db.commit()
        db.refresh(cycle)

        for auditor_id in audit_in.auditor_ids:
            AuditService.add_assignment(db, cycle.id, AssignmentCreate(auditor_id=auditor_id), actor, commit=False)

        for asset_id in audit_in.asset_ids:
            AuditService.add_finding(db, cycle.id, FindingCreate(asset_id=asset_id), actor, commit=False)

        db.commit()
        db.refresh(cycle)

        # Log action
        LogService.create(
            db=db,
            user_id=actor.id,
            action="create_audit",
            module="Audits",
            description=f"Created audit cycle {cycle.title}",
            role=actor.role,
            entity_id=cycle.id,
            status="success"
        )
        return cycle

    @staticmethod
    def add_assignment(db: Session, cycle_id: uuid.UUID, assignment_in: AssignmentCreate, actor: User, commit: bool = True):
        if actor.role not in MANAGE_AUDIT_ROLES:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        cycle = AuditService.get_by_id(db, cycle_id)
        if cycle.status == "closed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Audit cycle is closed")
        auditor = db.query(User).filter(User.id == assignment_in.auditor_id, User.status == "active").first()
        if not auditor:
            raise HTTPException(status_code=404, detail="Auditor not found")
        existing = db.query(AuditAssignment).filter(
            AuditAssignment.audit_cycle_id == cycle_id,
            AuditAssignment.auditor_id == assignment_in.auditor_id,
        ).first()
        if existing:
            return existing
        assignment = AuditAssignment(audit_cycle_id=cycle_id, auditor_id=assignment_in.auditor_id)
        db.add(assignment)
        if commit:
            db.commit()
            db.refresh(assignment)
        return assignment

    @staticmethod
    def add_finding(db: Session, cycle_id: uuid.UUID, finding_in: FindingCreate, actor: User, commit: bool = True):
        if actor.role not in MANAGE_AUDIT_ROLES:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        cycle = AuditService.get_by_id(db, cycle_id)
        if cycle.status == "closed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Audit cycle is closed")
        if not db.query(Asset).filter(Asset.id == finding_in.asset_id).first():
            raise HTTPException(status_code=404, detail="Asset not found")
        status_value = finding_in.status.lower()
        if status_value not in FINDING_STATUSES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid finding status")
        existing = db.query(AuditFinding).filter(
            AuditFinding.audit_cycle_id == cycle_id,
            AuditFinding.asset_id == finding_in.asset_id,
        ).first()
        if existing:
            return existing
        finding = AuditFinding(
            audit_cycle_id=cycle_id,
            asset_id=finding_in.asset_id,
            status=status_value,
            notes=finding_in.notes,
        )
        db.add(finding)
        if commit:
            db.commit()
            db.refresh(finding)
        return finding

    @staticmethod
    def update_finding(db: Session, cycle_id: uuid.UUID, finding_id: uuid.UUID, finding_in: FindingUpdate, actor: User):
        cycle = AuditService.get_by_id(db, cycle_id)
        if cycle.status == "closed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Audit cycle is closed")
        assigned = actor.role in MANAGE_AUDIT_ROLES or db.query(AuditAssignment).filter(
            AuditAssignment.audit_cycle_id == cycle_id,
            AuditAssignment.auditor_id == actor.id,
        ).first()
        if not assigned:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        finding = db.query(AuditFinding).filter(
            AuditFinding.id == finding_id,
            AuditFinding.audit_cycle_id == cycle_id
        ).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Audit finding record not found")

        new_status = finding_in.status.lower()
        if new_status not in FINDING_STATUSES or new_status == "pending":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid finding status")
        finding.status = new_status
        finding.notes = finding_in.notes
        finding.auditor_id = actor.id
        finding.verified_at = datetime.utcnow()

        db.commit()
        db.refresh(finding)

        # Generate alert if discrepancies found (damaged or missing)
        if finding.status in ["damaged", "missing"]:
            # Send notification to the auditor/manager
            NotificationService.create(
                db=db,
                user_id=actor.id,
                notification_type="audit",
                title="Audit Discrepancy",
                message=f"Asset {finding.asset_id} marked as {finding.status} during audit.",
                link=f"/audits/{cycle_id}"
            )

        # Log action
        LogService.create(
            db=db,
            user_id=actor.id,
            action="update_finding",
            module="Audits",
            description=f"Marked asset {finding.asset_id} finding as {finding.status}",
            role=actor.role,
            entity_id=finding.id,
            status="success"
        )
        return finding

    @staticmethod
    def close_cycle(db: Session, cycle_id: uuid.UUID, actor: User):
        if actor.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can close audit cycles")
        cycle = AuditService.get_by_id(db, cycle_id)
        if cycle.status == "closed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Audit cycle is already closed")

        cycle.status = "closed"

        for finding in cycle.findings:
            if finding.status == "missing":
                asset = db.query(Asset).filter(Asset.id == finding.asset_id).first()
                if asset:
                    asset.status = "lost"

        db.commit()
        db.refresh(cycle)

        # Log action
        LogService.create(
            db=db,
            user_id=actor.id,
            action="close_audit",
            module="Audits",
            description=f"Closed audit cycle {cycle.title}",
            role=actor.role,
            entity_id=cycle.id,
            status="success"
        )
        for assignment in cycle.assignments:
            NotificationService.create(
                db=db,
                user_id=assignment.auditor_id,
                notification_type="audit",
                title="Audit closed",
                message=f"Audit cycle {cycle.title} has been closed.",
                link=f"/audits/{cycle.id}",
            )
        return cycle
