"""
One-time script: Creates the MySQL database if it doesn't exist.
Run BEFORE starting the backend for the first time with MySQL.

Usage:
    python init_mysql.py

Note: Update the connection variables below to match your MySQL setup.
"""

import pymysql
import sys

# ── MySQL Connection Details ──────────────────────────────────
# Update these to match your local MySQL server configuration.
HOST = "localhost"
PORT = 3306
USER = "root"
PASSWORD = "12345678"
DB_NAME = "plagiarism_db"


def main():
    print(f"Connecting to MySQL server at {HOST}:{PORT} as '{USER}'...")

    try:
        conn = pymysql.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
        )
    except pymysql.err.OperationalError as e:
        print(f"\n❌ Failed to connect to MySQL server: {e}")
        print("\nPlease ensure:")
        print("  1. MySQL server is running")
        print("  2. The username/password above are correct")
        print("  3. The MySQL server is accepting connections on the specified host/port")
        sys.exit(1)

    try:
        cursor = conn.cursor()

        # Create database with utf8mb4 charset (supports full Unicode including emojis)
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        print(f"[OK] Database '{DB_NAME}' created (or already exists).")

        # Verify the database exists
        cursor.execute("SHOW DATABASES")
        databases = [row[0] for row in cursor.fetchall()]
        if DB_NAME in databases:
            print(f"[OK] Verified: '{DB_NAME}' is listed in SHOW DATABASES.")
        else:
            print(f"[WARNING] '{DB_NAME}' not found after creation attempt.")

        cursor.close()
        conn.close()

        print(f"\n[NEXT STEPS]")
        print(f"   1. Ensure your backend/.env has: DATABASE_URL=mysql://root:12345678@localhost:3306/{DB_NAME}")
        print(f"   2. Start the backend:  python -m uvicorn main:app --port 8000 --reload")
        print(f"   3. Tables will be auto-created on startup via SQLAlchemy create_all().")
        print(f"   4. Seed demo users:    python seed_users.py")

    except Exception as e:
        print(f"\n[ERROR] Error during database creation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
