import uuid
from sqlalchemy.orm import Session
from app.core import security
from app.models.organization import Department, AssetCategory
from app.models.user import User

# Stable UUID generator for seed values
def seed_uuid(seed_id: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"{seed_id}.assetflow.local")

def seed_db(db: Session):
    # 1. Seed Categories if empty
    if db.query(AssetCategory).count() == 0:
        categories = [
            AssetCategory(id=seed_uuid("c1"), name="Electronics", description="Laptops, phones, tablets", status="active"),
            AssetCategory(id=seed_uuid("c2"), name="Furniture", description="Chairs, desks, cabinets", status="active"),
            AssetCategory(id=seed_uuid("c3"), name="Vehicles", description="Company vehicles", status="active"),
            AssetCategory(id=seed_uuid("c4"), name="Rooms", description="Bookable rooms", status="active"),
            AssetCategory(id=seed_uuid("c5"), name="Equipment", description="Projectors, printers", status="active"),
            AssetCategory(id=seed_uuid("c6"), name="Software", description="Software licenses", status="active"),
        ]
        db.add_all(categories)
        db.commit()

    # 2. Seed Departments if empty
    if db.query(Department).count() == 0:
        departments = [
            Department(id=seed_uuid("d1"), name="Information Technology", code="IT", status="active"),
            Department(id=seed_uuid("d2"), name="Human Resources", code="HR", status="active"),
            Department(id=seed_uuid("d3"), name="Finance", code="FIN", status="active"),
            Department(id=seed_uuid("d4"), name="Operations", code="OPS", status="active"),
            Department(id=seed_uuid("d5"), name="Administration", code="ADM", status="active"),
        ]
        db.add_all(departments)
        db.commit()

    # 3. Seed Users if empty
    if db.query(User).count() == 0:
        default_pwd_hash = security.get_password_hash("password123")
        users = [
            User(id=seed_uuid("e1"), name="Anita Rao", email="anita.rao@assetflow.co", hashed_password=default_pwd_hash, role="admin", department_id=seed_uuid("d5"), status="active"),
            User(id=seed_uuid("e2"), name="Raj Mehta", email="raj.mehta@assetflow.co", hashed_password=default_pwd_hash, role="asset_manager", department_id=seed_uuid("d1"), status="active"),
            User(id=seed_uuid("e3"), name="Priya Shah", email="priya.shah@assetflow.co", hashed_password=default_pwd_hash, role="employee", department_id=seed_uuid("d1"), status="active"),
            User(id=seed_uuid("e4"), name="Arjun Nair", email="arjun.nair@assetflow.co", hashed_password=default_pwd_hash, role="employee", department_id=seed_uuid("d1"), status="active"),
            User(id=seed_uuid("e5"), name="Sneha Iyer", email="sneha.iyer@assetflow.co", hashed_password=default_pwd_hash, role="department_head", department_id=seed_uuid("d2"), status="active"),
            User(id=seed_uuid("e6"), name="Vikram Desai", email="vikram.desai@assetflow.co", hashed_password=default_pwd_hash, role="employee", department_id=seed_uuid("d2"), status="active"),
            User(id=seed_uuid("e7"), name="Meera Kulkarni", email="meera.kulkarni@assetflow.co", hashed_password=default_pwd_hash, role="department_head", department_id=seed_uuid("d3"), status="active"),
            User(id=seed_uuid("e8"), name="Rohit Verma", email="rohit.verma@assetflow.co", hashed_password=default_pwd_hash, role="employee", department_id=seed_uuid("d3"), status="active"),
            User(id=seed_uuid("e9"), name="Kavita Menon", email="kavita.menon@assetflow.co", hashed_password=default_pwd_hash, role="department_head", department_id=seed_uuid("d4"), status="active"),
            User(id=seed_uuid("e10"), name="Sanjay Pillai", email="sanjay.pillai@assetflow.co", hashed_password=default_pwd_hash, role="employee", department_id=seed_uuid("d4"), status="active"),
            User(id=seed_uuid("e11"), name="Divya Krishnan", email="divya.krishnan@assetflow.co", hashed_password=default_pwd_hash, role="asset_manager", department_id=seed_uuid("d5"), status="active"),
            User(id=seed_uuid("e12"), name="Aditya Bose", email="aditya.bose@assetflow.co", hashed_password=default_pwd_hash, role="employee", department_id=seed_uuid("d5"), status="active"),
        ]
        for u in users:
            db.add(u)
            db.commit()

        # Update department heads to point to the created users
        d1 = db.query(Department).filter(Department.id == seed_uuid("d1")).first()
        if d1:
            d1.head_id = seed_uuid("e2")
        
        d2 = db.query(Department).filter(Department.id == seed_uuid("d2")).first()
        if d2:
            d2.head_id = seed_uuid("e5")
        
        d3 = db.query(Department).filter(Department.id == seed_uuid("d3")).first()
        if d3:
            d3.head_id = seed_uuid("e7")
        
        d4 = db.query(Department).filter(Department.id == seed_uuid("d4")).first()
        if d4:
            d4.head_id = seed_uuid("e9")
        
        d5 = db.query(Department).filter(Department.id == seed_uuid("d5")).first()
        if d5:
            d5.head_id = seed_uuid("e11")
        
        db.commit()
