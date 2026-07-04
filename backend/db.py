import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# Pluggable DATABASE_URL (default to local sqlite database)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./evaluation_platform.db")

# Detect if we are using SQLite
is_sqlite = DATABASE_URL.startswith("sqlite")

connect_args = {}
if is_sqlite:
    # Ensure multi-threaded access works cleanly in SQLite
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

# SQLite-specific performance tuning (WAL mode and busy timeout)
if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency helper for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
