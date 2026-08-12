"""
Central database connection point for AgriSense.
Supports MySQL (default) with automatic database creation and graceful SQLite fallback.
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


def create_db_engine():
    """
    Initializes SQLAlchemy engine.
    1. Tries connecting to MySQL with the specified database.
    2. If the database does not exist, attempts to create it on MySQL.
    3. If MySQL is unreachable, falls back gracefully to a local SQLite database.
    """
    mysql_url = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )
    try:
        engine = create_engine(mysql_url, echo=False, pool_pre_ping=True, pool_recycle=3600)
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        print("[DB] Connected to MySQL database successfully.")
        return engine
    except Exception as e:
        # Try auto-creating the MySQL database if server is up
        try:
            server_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/?charset=utf8mb4"
            root_engine = create_engine(server_url)
            with root_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            engine = create_engine(mysql_url, echo=False, pool_pre_ping=True, pool_recycle=3600)
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            print(f"[DB] Created and connected to MySQL database '{DB_NAME}'.")
            return engine
        except Exception as err2:
            print(f"[DB] MySQL server unreachable ({e}). Falling back to SQLite ('agrisense.db').")
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, "agrisense.db")
            sqlite_url = f"sqlite:///{db_path}"
            return create_engine(sqlite_url, echo=False)


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

