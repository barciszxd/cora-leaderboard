"""Database connection and session management for Flask application"""
import atexit
import functools
import logging
import time

from config import config
from flask import g
from sqlalchemy import create_engine
from sqlalchemy.exc import DisconnectionError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Create database engine with more robust connection settings
engine = create_engine(
    config.DATABASE_URL,
    echo          = False,
    poolclass     = QueuePool,
    pool_size     = 5,
    max_overflow  = 10,
    pool_pre_ping = True,
    pool_recycle  = 1800,
    pool_timeout  = 30,
    connect_args  = {
        "connect_timeout": 30,
        "application_name": "cora_leaderboard",
        "options": "-c statement_timeout=30000",
        "keepalives_idle": "600",
        "keepalives_interval": "30",
        "keepalives_count": "3"
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session:
    """Get or create a database session for the current request"""
    if 'db_session' not in g:
        g.db_session = SessionLocal()
    return g.db_session


def close_db_session(error=None) -> None:
    """Close the database session at the end of the request"""
    session = g.pop('db_session', None)
    if session is not None:
        try:
            if error is None:
                session.commit()
            else:
                session.rollback()
        except SQLAlchemyError as e:
            logger.error("Error closing session: %s", e)
            session.rollback()
        finally:
            session.close()


def cleanup_db_connections():
    """Close all database connections when the application shuts down"""
    try:
        engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error("Error closing database connections: %s", e)


atexit.register(cleanup_db_connections)


def retry_db_operation(max_retries=3, delay=1):
    """Decorator to retry database operations on connection failures"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DisconnectionError) as e:
                    if attempt == max_retries - 1:
                        logger.error("Database operation failed after %d attempts: %s", max_retries, e)
                        raise
                    logger.warning("Database operation failed (attempt %d/%d): %s", attempt + 1, max_retries, e)
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
                except Exception as e:
                    logger.error("Non-recoverable database error: %s", e)
                    raise
            return None
        return wrapper
    return decorator


@retry_db_operation(max_retries=3, delay=2)
def init_db():
    """Initialize database tables with retry logic"""
    try:
        from app.models import Base
        from app.models.athlete import Athlete
        from app.models.challenge import Challenge
        from app.models.effort import Effort
        from app.models.segment import Segment

        logger.info("Attempting to create database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        raise
