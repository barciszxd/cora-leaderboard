"""Module containing the Challenge model for the Cora Leaderboard application."""
from datetime import datetime, timezone

from app.models import Base
from sqlalchemy import Column, DateTime, Integer


class Challenge(Base):
    """Database model for a challenge on the Cora Leaderboard."""
    __tablename__ = "challenges"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    climb_segment_id  = Column(Integer, nullable=False)
    sprint_segment_id = Column(Integer, nullable=False)
    start_date        = Column(DateTime(timezone=True), nullable=False)
    end_date          = Column(DateTime(timezone=True), nullable=False)
    created_at        = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at        = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
