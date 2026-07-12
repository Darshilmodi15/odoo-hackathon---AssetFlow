import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.asset import Asset
from app.models.audit import AuditCycle, AuditAssignment, AuditFinding
from app.models.user import User
from app.schemas.audit import AuditCreate, FindingUpdate
from app.services.notification import NotificationService
from app.services.log import LogService

class AuditService:
    @staticmethod
    def get_all(db: Session):
        return db.query(AuditCycle).all()

    @staticmethod
    def create(db: Session, audit_in: AuditCreate, actor: User):
        # 1. Create audit cycle
        cycle = AuditCycle(
            title=audit_in.title,
            scope_department_id=audit_in.scope_department_id,
            scope_location=audit_in.scope_location,
            start_date=audit_in.start_date,
            end_date=audit_in.end_date,
            status="active"  # Start immediately as active for testing
        )
        db.add(cycle)
        db.commit()
        db.refresh(cycle)

        # 2. Add auditor assignments
        for auditor_id in audit_in.auditor_ids:
            assign = AuditAssignment(
                audit_cycle_id=cycle.id,
                auditor_id=auditor_id
            )
            db.add(assign)

        # 3. Add audit findings for scoped assets
        for asset_id in audit_in.asset_ids:
            finding = AuditFinding(
                audit_cycle_id=cycle.id,
                asset_id=asset_id,
                status="pending"
            )
            db.add(finding)

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
    def update_finding(db: Session, cycle_id: uuid.UUID, finding_id: uuid.UUID, finding_in: FindingUpdate, actor: User):
        # 1. Get finding
        finding = db.query(AuditFinding).filter(
            AuditFinding.id == finding_id,
            AuditFinding.audit_cycle_id == cycle_id
        ).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Audit finding record not found")

        finding.status = finding_in.status.lower()
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
        cycle = db.query(AuditCycle).filter(AuditCycle.id == cycle_id).first()
        if not cycle:
            raise HTTPException(status_code=404, detail="Audit cycle not found")

        cycle.status = "closed"

        # Auto-update status of confirmed missing assets to 'lost'
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
        return cycle
