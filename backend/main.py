"""
FastAPI Application Entry Point.

This is the main server file. It:
  - Creates the FastAPI app
  - Configures CORS for the React frontend
  - Includes all API routers
  - Auto-creates database tables on startup
  - Configures structured logging
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import engine, Base
from core.config import get_settings

# ── Import all models so SQLAlchemy sees them ────────────────
from models.user import User
from models.submission import Submission
from models.report import Report

# ── Import API routers ────────────────────────────────────────
from api.auth import router as auth_router
from api.submissions import router as submissions_router
from api.status import router as status_router
from api.reports import router as reports_router
from api.analytics import router as analytics_router


settings = get_settings()

# ── Configure Logging ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup/shutdown events) ────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup, cleanup on shutdown."""
    logger.info("🚀 Starting PlagiarismAI Backend...")

    # Create uploads directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Create all database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created / verified.")
    except Exception as e:
        logger.error(f"⚠️ Database connection failed: {e}")
        logger.warning("Server will start but DB-dependent routes will fail until DB is available.")

    yield

    logger.info("🛑 Shutting down PlagiarismAI Backend.")


# ── FastAPI App ───────────────────────────────────────────────
app = FastAPI(
    title="PlagiarismAI — Assignment Evaluation Backend",
    description=(
        "Production-ready backend for AI-powered assignment plagiarism detection. "
        "Processes submissions asynchronously via Celery workers."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ───────────────────────────────────────────
# Allow local frontend dev servers to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ─────────────────────────────────────────
app.include_router(auth_router)
app.include_router(submissions_router)
app.include_router(status_router)
app.include_router(reports_router)
app.include_router(analytics_router)



# ── Health Check ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health_check():
    return {
        "service": "PlagiarismAI Backend",
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/api/health", tags=["Health"])
def api_health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    # Default local run settings so frontend can connect consistently.
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
