import os
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import Session, engine
from app.models.user import User


def main() -> int:
    email = os.getenv("INITIAL_ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("INITIAL_ADMIN_PASSWORD", "")
    name = os.getenv("INITIAL_ADMIN_NAME", "Initial Admin").strip() or "Initial Admin"
    if not email or not password:
        print("Admin seed skipped: INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD are required.")
        return 1
    with Session(engine) as db:
        existing = db.scalar(select(User).where(User.email == email))
        if existing:
            changed = False
            if existing.role != "admin":
                existing.role = "admin"
                changed = True
            if existing.status != "active":
                existing.status = "active"
                changed = True
            if changed:
                db.commit()
            print("Admin seed complete: existing admin user is ready.")
            return 0
        db.add(User(name=name, email=email, hashed_password=hash_password(password), role="admin", status="active"))
        db.commit()
        print("Admin seed complete: admin user created.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
