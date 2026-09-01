"""
RecoverOS FastAPI Application — Phase 1 Modularized Backend
AI Revenue Recovery Decision Engine — Razorpay Buildathon Track 03
"""

import os
import sys
from contextlib import asynccontextmanager

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database initialization
from db.database import init_db
from utils.logger import setup_logger

# Import API Routers
from api.health import router as health_router
from api.cases import router as cases_router
from api.batch import router as batch_router
from api.demo import router as demo_router
from api.webhooks import router as webhooks_router
from api.auth import router as auth_router

logger = setup_logger("recoveros.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for database initialization and service cleanup."""
    logger.info("Initializing RecoverOS Backend Services...")
    try:
        init_db()
        logger.info("Database schemas verified and connected.")
    except Exception as err:
        logger.error(f"Database initialization warning: {err}")
    yield
    logger.info("RecoverOS Backend Services shutting down cleanly.")


app = FastAPI(
    title="RecoverOS",
    description="AI Revenue Recovery Decision Engine — Razorpay Buildathon Track 03",
    version="0.3.0-phase3-detectors",
    lifespan=lifespan
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Modular API Routers
app.include_router(health_router)
app.include_router(cases_router)
app.include_router(batch_router)
app.include_router(demo_router)
app.include_router(webhooks_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "system": "RecoverOS AI Revenue Recovery Engine",
        "phase": "Phase 1: Backend Modularization & Persistence Layer",
        "docs_url": "/docs",
        "health_check": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)