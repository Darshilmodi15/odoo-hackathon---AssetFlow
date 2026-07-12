from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import settings

# Attempt to connect to the configured database, fall back to SQLite if it fails
db_url = settings.database_url
engine = None
db_type = "postgresql"

if db_url.startswith("postgresql"):
    try:
        # Quick test connection
        temp_engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        conn = temp_engine.connect()
        conn.close()
        engine = temp_engine
    except Exception as e:
        print(f"Warning: PostgreSQL connection failed ({e}). Falling back to local SQLite database.")
        db_url = "sqlite:///./assetflow.db"
        db_type = "sqlite"

if engine is None:
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=300,
    ).execution_options(insertmanyvalues=False)
    if db_url.startswith("sqlite"):
        db_type = "sqlite"

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

# Alias for backward compatibility
get_db = get_session
