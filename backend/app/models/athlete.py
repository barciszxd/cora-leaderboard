"""Module containing the Athlete model for the Cora Leaderboard application."""
from datetime import datetime, timezone

from app.models import Base
from sqlalchemy import Column, DateTime, Integer, String


class Athlete(Base):
    """Database model for an athlete on the Cora Leaderboard."""
    __tablename__ = 'athletes'

    id            = Column(Integer, primary_key=True)  # Strava athlete ID
    firstname     = Column(String(100))
    lastname      = Column(String(100))
    sex           = Column(String(1))
    access_token  = Column(String(255))
    refresh_token = Column(String(255))
    expires_at    = Column(Integer)  # Unix timestamp
    token_type    = Column(String(20), default='Bearer')
    created_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
