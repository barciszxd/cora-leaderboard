"""Module containing the Athlete model for the Cora Leaderboard application."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Efforts(Base):
    """Database model for athlete efforts."""
    __tablename__ = 'efforts'

    id            = Column(Integer, primary_key=True)  # Unique ID for the effort
    athlete_id    = Column(Integer, nullable=False)  # Foreign key to Athlete
    segment_id    = Column(Integer, nullable=False)  # Foreign key to Segment
    start_date    = Column(DateTime, nullable=False)  # Start date of the effort
    elapsed_time  = Column(Integer, nullable=False)  # Elapsed time in seconds
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
