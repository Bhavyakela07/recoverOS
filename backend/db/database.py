"""
RecoverOS Database Layer — SQLAlchemy Engine & Session Configuration
Supports explicit PostgreSQL or intentional SQLite configuration without silent error masking.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("recoveros.db")

# Read database URL or default to local SQLite database explicitly
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recoveros.db")

# Create engine with explicit configuration and error handling
if DATABASE_URL.startswith("postgresql"):
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        with engine.connect() as conn:
            logger.info("Successfully connected to primary PostgreSQL database.")
    except Exception as err:
        logger.error(f"Failed to connect to configured PostgreSQL database: {err}")
        raise RuntimeError(f"PostgreSQL Database connection failed: {err}")
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    logger.info(f"Initialized SQLite database at {DATABASE_URL}")

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
    import db.models  # Ensures all ORM models are registered in Base.metadata
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
