from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api import deps
from app.models.user import User
from app.schemas.audit import AuditCreate, FindingUpdate, FindingResponse, AuditResponse
from app.services.audit import AuditService

router = APIRouter()

@router.get("", response_model=List[AuditResponse])
def get_audit_cycles(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    List all audit cycles.
    """
    return AuditService.get_all(db)

@router.post("", response_model=AuditResponse, status_code=status.HTTP_201_CREATED)
def create_audit_cycle(
    audit_in: AuditCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create a new audit cycle with auditor assignments and asset findings.
    """
    return AuditService.create(db, audit_in, current_user)

@router.put("/{cycle_id}/findings/{finding_id}", response_model=FindingResponse)
def update_audit_finding(
    cycle_id: uuid.UUID,
    finding_id: uuid.UUID,
    finding_in: FindingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update the finding status for a specific asset in an audit cycle.
    """
    return AuditService.update_finding(db, cycle_id, finding_id, finding_in, current_user)

@router.post("/{id}/close", response_model=AuditResponse)
def close_audit_cycle(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Close the audit cycle, locking status and updating missing assets to lost.
    """
    return AuditService.close_cycle(db, id, current_user)
