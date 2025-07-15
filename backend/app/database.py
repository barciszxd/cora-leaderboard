from config import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(config.DATABASE_URL, echo=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create session instance
db_session = SessionLocal()


def init_db():
    """Initialize database tables"""
    from app.models.athlete import Base
    Base.metadata.create_all(bind=engine)
