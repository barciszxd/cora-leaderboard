"""Athlete Repository Module"""
from app.models.athlete import Athlete
from sqlalchemy.orm import Session


class AthleteRepository:
    """Repository for managing Athlete records in the database."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, athlete_data: dict, token_data: dict) -> Athlete:
        """Create a new athlete."""
        athlete = Athlete(
            id            = athlete_data['id'],
            firstname     = athlete_data.get('firstname'),
            lastname      = athlete_data.get('lastname'),
            access_token  = token_data.get('access_token'),
            refresh_token = token_data.get('refresh_token'),
            expires_at    = token_data.get('expires_at'),
            token_type    = token_data.get('token_type', 'Bearer')
        )
        self.session.add(athlete)
        return athlete

    def update(self, athlete: Athlete, athlete_data: dict, token_data: dict) -> Athlete | None:
        """Update an existing athlete."""
        athlete.firstname     = athlete_data.get('firstname', athlete.firstname)
        athlete.lastname      = athlete_data.get('lastname', athlete.lastname)
        athlete.access_token  = token_data.get('access_token', athlete.access_token)
        athlete.refresh_token = token_data.get('refresh_token', athlete.refresh_token)
        athlete.expires_at    = token_data.get('expires_at', athlete.expires_at)

        return athlete

    def get_by_id(self, athlete_id: int) -> Athlete | None:
        """Get athlete by ID."""
        return self.session.query(Athlete).filter_by(id=athlete_id).first()
