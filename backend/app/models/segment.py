"""Module containing the Segment model for the Cora Leaderboard application."""
from datetime import datetime, timezone

from app.models import Base
from sqlalchemy import Column, DateTime, Float, Integer, String


class Segment(Base):
    """Database model for a segment on the Cora Leaderboard."""
    __tablename__ = 'segments'

    id             = Column(Integer, primary_key=True)  # Segment ID on strava
    name           = Column(String(100))
    distance       = Column(Float)  # Distance in meters
    elevation_gain = Column(Float)  # Elevation gain in meters
    created_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
