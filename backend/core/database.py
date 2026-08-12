"""
SQLAlchemy database engine, session factory, and declarative Base.

Supports three database backends:
  - SQLite:      DATABASE_URL=sqlite:///./plagiarism.db      (zero-config dev)
  - MySQL:       DATABASE_URL=mysql://user:pass@host/db      (development/staging)
  - PostgreSQL:  DATABASE_URL=postgresql://user:pass@host/db  (production)
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
elif _db_url.startswith("mysql://"):
    _db_url = _db_url.replace("mysql://", "mysql+pymysql://", 1)

_is_sqlite = _db_url.startswith("sqlite")
_is_mysql = _db_url.startswith("mysql")

# ── Engine ────────────────────────────────────────────────────
if _is_sqlite:
    engine = create_engine(
        _db_url,
        connect_args={"check_same_thread": False},  # required for SQLite
        echo=False,
    )
    logger.info(f"Database engine: SQLite (dev mode)")
elif _is_mysql:
    engine = create_engine(
        _db_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,   # reconnect after 1 hour to avoid MySQL wait_timeout
        echo=False,
    )
    logger.info(f"Database engine: MySQL")
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
