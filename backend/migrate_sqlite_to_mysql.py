"""
Optional: Migrate existing data from SQLite (plagiarism.db) → MySQL.

This script reads all rows from the local SQLite database and inserts them
into the MySQL database, preserving IDs, timestamps, and relationships.

Prerequisites:
  1. MySQL database must already exist (run init_mysql.py first).
  2. Backend must have been started at least once with MySQL so that
     SQLAlchemy's create_all() has created the empty tables.

Usage:
    python migrate_sqlite_to_mysql.py
"""

import os
import sys
import logging

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format="%(asctime)s │ %(levelname)s │ %(message)s")
logger = logging.getLogger(__name__)

# ── Connection strings ────────────────────────────────────────
SQLITE_URL = "sqlite:///./plagiarism.db"
MYSQL_URL = "mysql+pymysql://root:password@localhost:3306/plagiarism_db"

# Tables to migrate in dependency order (parents before children)
TABLES = ["users", "submissions", "reports"]


def main():
    if not os.path.exists("plagiarism.db"):
        logger.error("plagiarism.db not found in the current directory. Nothing to migrate.")
        sys.exit(1)

    # ── Connect to both databases ─────────────────────────────
    sqlite_engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
    mysql_engine = create_engine(MYSQL_URL, pool_pre_ping=True)

    SrcSession = sessionmaker(bind=sqlite_engine)
    DstSession = sessionmaker(bind=mysql_engine)

    src = SrcSession()
    dst = DstSession()

    try:
        for table_name in TABLES:
            logger.info(f"Migrating table: {table_name}")

            # Read all rows from SQLite
            rows = src.execute(text(f"SELECT * FROM {table_name}")).fetchall()

            if not rows:
                logger.info(f"  → {table_name}: 0 rows (skipped)")
                continue

            # Get column names from the result
            columns = src.execute(text(f"SELECT * FROM {table_name} LIMIT 1")).keys()
            col_list = list(columns)

            # Build INSERT statement for MySQL
            col_names = ", ".join(f"`{c}`" for c in col_list)
            placeholders = ", ".join(f":{c}" for c in col_list)
            insert_sql = text(f"INSERT INTO `{table_name}` ({col_names}) VALUES ({placeholders})")

            # Insert rows into MySQL
            row_dicts = [dict(zip(col_list, row)) for row in rows]

            # Clear existing data in MySQL table first (in case of re-run)
            dst.execute(text(f"DELETE FROM `{table_name}`"))
            dst.commit()

            # Insert in batches
            batch_size = 100
            for i in range(0, len(row_dicts), batch_size):
                batch = row_dicts[i:i + batch_size]
                dst.execute(insert_sql, batch)
                dst.commit()

            logger.info(f"  → {table_name}: {len(rows)} rows migrated successfully")

        logger.info("="*50)
        logger.info("✅ Migration complete! All data transferred to MySQL.")
        logger.info("="*50)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        dst.rollback()
        sys.exit(1)
    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    main()
