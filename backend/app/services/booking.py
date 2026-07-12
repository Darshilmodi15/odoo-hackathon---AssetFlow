import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import Asset, Booking
from app.models.user import User
from app.schemas.booking import BookingCreate
from app.services.notification import NotificationService
from app.services.log import LogService

class BookingOverlapException(Exception):
    def __init__(self, message: str, suggestions: list):
        self.message = message
        self.suggestions = suggestions


class BookingService:
    @staticmethod
    def get_all(db: Session):
        return db.query(Booking).all()

    @staticmethod
    def create(db: Session, booking_in: BookingCreate, actor: User):
        # 1. Check if asset exists
        asset = db.query(Asset).filter(Asset.id == booking_in.asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # 2. Check overlap
        # overlap if start_at < booking.end_at and end_at > booking.start_at
        conflict = db.query(Booking).filter(
            Booking.asset_id == booking_in.asset_id,
            Booking.status != "cancelled",
            Booking.start_at < booking_in.end_at,
            Booking.end_at > booking_in.start_at
        ).first()

        if conflict:
            # Overlap found! Generate suggestions
            duration = booking_in.end_at - booking_in.start_at
            suggestions = []

            # Suggestion 1: Same resource, later time (right after conflict ends)
            later_start = conflict.end_at
            later_end = later_start + duration
            suggestions.append({
                "asset_id": str(booking_in.asset_id),
                "start_at": later_start.isoformat(),
                "end_at": later_end.isoformat(),
                "reason": "Same resource, later time"
            })

            # Suggestion 2: Alternate shared resource in the same category
            alts = db.query(Asset).filter(
                Asset.id != booking_in.asset_id,
                Asset.shared == True,
                Asset.category_id == asset.category_id
            ).all()

            for alt in alts:
                overlap_alt = db.query(Booking).filter(
                    Booking.asset_id == alt.id,
                    Booking.status != "cancelled",
                    Booking.start_at < booking_in.end_at,
                    Booking.end_at > booking_in.start_at
                ).first()
                if not overlap_alt:
                    suggestions.append({
                        "asset_id": str(alt.id),
                        "start_at": booking_in.start_at.isoformat(),
                        "end_at": booking_in.end_at.isoformat(),
                        "reason": f"Alternative: {alt.name}"
                    })
                    break

            raise BookingOverlapException(
                message="Resource is already booked during this time.",
                suggestions=suggestions
            )

        # 3. Create booking
        db_obj = Booking(
            asset_id=booking_in.asset_id,
            booked_by_id=actor.id,
            department_id=actor.department_id,
            start_at=booking_in.start_at,
            end_at=booking_in.end_at,
            purpose=booking_in.purpose,
            attendees=booking_in.attendees,
            notes=booking_in.notes,
            status="upcoming"
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # Log action
        LogService.create(
            db=db,
            user_id=actor.id,
            action="create_booking",
            module="Bookings",
            description=f"Booked shared resource {asset.tag} for {db_obj.purpose}",
            role=actor.role,
            entity_id=db_obj.id,
            status="success"
        )
        return db_obj

    @staticmethod
    def cancel(db: Session, booking_id: uuid.UUID, actor: User):
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        booking.status = "cancelled"
        db.commit()
        db.refresh(booking)

        # Log action
        LogService.create(
            db=db,
            user_id=actor.id,
            action="cancel_booking",
            module="Bookings",
            description=f"Cancelled booking {booking.id}",
            role=actor.role,
            entity_id=booking.id,
            status="success"
        )
        return booking
