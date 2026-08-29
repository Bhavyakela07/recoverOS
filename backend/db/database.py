"""
RecoverOS Database Layer — SQLAlchemy Engine & Session Configuration
Supports PostgreSQL with SQLite fallback for seamless execution across environments.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("recoveros.db")

# Default PostgreSQL database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://recoveros:recoveros_password@localhost:5432/recoveros"
)

# SQLite fallback URL
SQLITE_FALLBACK_URL = "sqlite:///./recoveros.db"

# Create engine with fallback logic
try:
    if DATABASE_URL.startswith("postgresql"):
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
    else:
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
    # Test connection
    with engine.connect() as conn:
        logger.info("Successfully connected to primary database.")
except Exception as err:
    logger.warning(f"Could not connect to PostgreSQL ({err}). Falling back to SQLite.")
    engine = create_engine(
        SQLITE_FALLBACK_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
