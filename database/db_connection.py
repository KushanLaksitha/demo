"""
Central database connection point for AgriSense.
Strictly uses MySQL with automatic database creation.
Reads credentials from a local .env file.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "vectamind_db")


def run_schema_migrations(engine):
    """
    Executes automatic schema updates (e.g. converting user_type to ENUM in MySQL,
    dropping legacy check constraints) to ensure seamless compatibility across all devices.
    """
    try:
        dial_name = engine.dialect.name
        if dial_name == "mysql":
            with engine.begin() as conn:
                try:
                    conn.execute(text("ALTER TABLE user DROP CHECK chk_user_type"))
                except Exception:
                    pass
                conn.execute(text("ALTER TABLE user MODIFY COLUMN user_type ENUM('farmer', 'trader', 'policymaker', 'admin') NOT NULL"))
            print("[DB Migration] MySQL user_type column updated to ENUM('farmer', 'trader', 'policymaker', 'admin').")
    except Exception as e:
        print(f"[DB Migration] Schema migration check: {e}")


def create_db_engine():
    """
    Initializes SQLAlchemy engine for MySQL.
    1. Tries connecting to MySQL with the specified database.
    2. If the database does not exist, attempts to create it on MySQL.
    3. If MySQL connection fails, raises an error.
    """
    mysql_url = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )
    try:
        eng = create_engine(mysql_url, echo=False, pool_pre_ping=True, pool_recycle=3600)
        with eng.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        print("[DB] Connected to MySQL database successfully.")
        run_schema_migrations(eng)
        return eng
    except Exception as e:
        # Try auto-creating the MySQL database if server is up
        try:
            server_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/?charset=utf8mb4"
            root_engine = create_engine(server_url)
            with root_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            eng = create_engine(mysql_url, echo=False, pool_pre_ping=True, pool_recycle=3600)
            with eng.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            print(f"[DB] Created and connected to MySQL database '{DB_NAME}'.")
            run_schema_migrations(eng)
            return eng
        except Exception as err2:
            print(f"[DB] ERROR: MySQL server unreachable: {err2} (initial error: {e})")
            raise RuntimeError(f"Failed to connect to MySQL database: {err2}") from err2


engine = create_db_engine()
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))


def get_session():
    """Return a thread-safe SQLAlchemy session."""
    return SessionLocal()


def safe_query(fn, default=None):
    """
    Runs a zero-arg callable that does DB work and returns its result.
    If any DB error occurs, logs it and returns `default`.
    """
    try:
        return fn()
    except Exception as e:
        print(f"[DB] Query failed, returning default. Reason: {e}")
        return default


def test_connection() -> bool:
    """Quick health check used on app startup."""
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception as e:
        print(f"[DB] Connection failed: {e}")
        return False


class DatabaseUnavailable(Exception):
    """Raised by data_service/auth_service helpers when DB can't be reached."""
    pass

