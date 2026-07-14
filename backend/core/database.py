"""
SQLAlchemy database engine, session factory, and declarative Base.

Uses SQLite as a zero-config fallback for local development.
Set DATABASE_URL=sqlite:///./plagiarism.db in .env for SQLite mode.
Set DATABASE_URL=postgresql://user:pass@host/db for production PostgreSQL.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Resolve connection URL ────────────────────────────────────
_db_url = settings.DATABASE_URL

if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)

_is_sqlite = _db_url.startswith("sqlite")

# ── Engine ────────────────────────────────────────────────────
if _is_sqlite:
    engine = create_engine(
        _db_url,
        connect_args={"check_same_thread": False},  # required for SQLite
        echo=False,
    )
    logger.info(f"Database engine: SQLite (dev mode)")
else:
    engine = create_engine(
        _db_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )
    logger.info(f"Database engine: PostgreSQL (production mode)")

# ── Session Factory ───────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ── Declarative Base ──────────────────────────────────────────
Base = declarative_base()
