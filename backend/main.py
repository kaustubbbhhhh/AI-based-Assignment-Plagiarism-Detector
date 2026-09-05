"""
FastAPI Application Entry Point.

This is the main server file. It:
  - Creates the FastAPI app
  - Configures CORS for the React frontend
  - Includes all API routers
  - Auto-creates and safely auto-migrates database tables on startup
  - Configures structured logging
"""

import os
import warnings
import logging

# Suppress PyTorch CUDA pynvml deprecation and Hugging Face warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="torch.cuda")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
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


def _ensure_schema_columns():
    """Safely adds new columns to existing database tables if they do not exist."""
    with engine.connect() as conn:
        # Columns to check and add for submissions table
        submission_cols = [
            ("assignment_title", "VARCHAR(200) DEFAULT 'Assignment 1'"),
            ("is_locked", "BOOLEAN DEFAULT 0"),
            ("locked_at", "DATETIME NULL"),
            ("verification_token", "VARCHAR(100) NULL"),
        ]
        for col_name, col_type in submission_cols:
            try:
                conn.execute(text(f"ALTER TABLE submissions ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                logger.info(f"Schema migrated: Added submissions.{col_name}")
            except Exception:
                pass  # column already exists or table not yet created

        # Columns to check and add for reports table
        report_cols = [
            ("ocr_score", "FLOAT DEFAULT 100.0"),
            ("ocr_status", "VARCHAR(100) DEFAULT 'Accepted'"),
        ]
        for col_name, col_type in report_cols:
            try:
                conn.execute(text(f"ALTER TABLE reports ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                logger.info(f"Schema migrated: Added reports.{col_name}")
            except Exception:
                pass


# ── Lifespan (startup/shutdown events) ────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup, cleanup on shutdown."""
    logger.info("🚀 Starting PlagiarismAI Backend...")
    if settings.APP_ENV.lower() != "development" and settings.SECRET_KEY == "dev-secret-key-do-not-use-in-production":
        raise RuntimeError("Insecure SECRET_KEY is not allowed outside development.")

    # Create uploads directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Create all database tables
    try:
        Base.metadata.create_all(bind=engine)
        _ensure_schema_columns()
        logger.info("✅ Database tables created & verified.")
    except Exception as e:
        logger.error(f"⚠️ Database connection / migration notice: {e}")
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
