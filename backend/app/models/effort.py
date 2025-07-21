"""Module containing the Athlete model for the Cora Leaderboard application."""
from datetime import datetime, timezone

from app.models import Base
from sqlalchemy import BigInteger, Column, DateTime, Integer


class Efforts(Base):
    """Database model for athlete efforts."""
    __tablename__ = 'efforts'

    id            = Column(BigInteger, primary_key=True)  # Unique identifier for the effort
    athlete_id    = Column(Integer, nullable=False)  # Foreign key to Athlete
    activity_id   = Column(BigInteger, nullable=False)  # Foreign key to Activity
    segment_id    = Column(Integer, nullable=False)  # Foreign key to Segment
    start_date    = Column(DateTime, nullable=False)  # Start date of the effort
    elapsed_time  = Column(Integer, nullable=False)  # Elapsed time in seconds
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
