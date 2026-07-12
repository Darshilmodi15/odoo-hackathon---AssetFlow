from sqlalchemy.orm import Session
from app.models.inquiry import Inquiry
from app.schemas.inquiry import InquiryCreate

class InquiryService:
    @staticmethod
    def create(db: Session, inquiry_in: InquiryCreate) -> Inquiry:
        db_obj = Inquiry(
            name=inquiry_in.name,
            email=inquiry_in.email,
            company=inquiry_in.company,
            message=inquiry_in.message,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
