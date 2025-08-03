"""Database connection and session management for Flask application"""
import functools
import logging
import time

from config import config
from flask import g, jsonify
from sqlalchemy import create_engine
from sqlalchemy.exc import DisconnectionError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    config.DATABASE_URL,
    echo=True,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "connect_timeout": 10,
        "application_name": "cora_leaderboard"
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


def retry_db_operation(max_retries=3, delay=1):
    """Decorator to retry database operations on connection failures"""
    def decorator(func):
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


def handle_db_exceptions(f):
    """Decorator to handle database exceptions in API routes."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (OperationalError, DisconnectionError) as e:
            logger.error("Database connection issue in %s: %s", f.__name__, e)
            return jsonify({
                "success": False,
                "error": "Database connection issue. Please try again.",
                "details": str(e)
            }), 503
        except Exception as e:
            logger.error("Unexpected error in %s: %s", f.__name__, e)
            return jsonify({
                "success": False,
                "error": "Internal server error. Please try again.",
                "details": str(e)
            }), 500
    return decorated_function


def init_db():
    """Initialize database tables"""
    from app.models import Base
    from app.models.athlete import Athlete
    from app.models.challenge import Challenge
    from app.models.effort import Effort
    from app.models.segment import Segment
    Base.metadata.create_all(bind=engine)
