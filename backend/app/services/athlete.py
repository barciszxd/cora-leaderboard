"""Athlete Repository Module"""
from datetime import datetime, timezone

import requests

from app.models.athlete import Athlete
from config import config
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

    def delete_by_id(self, athlete_id: int) -> bool:
        """Delete athlete by ID."""
        athlete = self.get_by_id(athlete_id)
        if athlete:
            self.session.delete(athlete)
            return True
        return False

    def update_token(self, athlete: Athlete, token_data: dict) -> Athlete:
        """Update the access token for an athlete."""
        athlete.access_token  = token_data.get('access_token', athlete.access_token)
        athlete.refresh_token = token_data.get('refresh_token', athlete.refresh_token)
        athlete.expires_at    = token_data.get('expires_at', athlete.expires_at)

        return athlete

    def get_by_id(self, athlete_id: int) -> Athlete | None:
        """Get athlete by ID."""
        return self.session.query(Athlete).filter_by(id=athlete_id).first()

    def get_access_token(self, athlete_id: int) -> str | None:
        """Get access token for an athlete.

        If the token is expired, get a new one and update the athlete record.

        Args:
            athlete_id (int): The ID of the athlete.

        Returns:
            str | None: The access token if available, otherwise None.
        """
        athlete = self.get_by_id(athlete_id)

        if not athlete:
            return None

        if athlete.expires_at < datetime.now(timezone.utc).timestamp():
            token_url = "https://www.strava.com/oauth/token"
            request_body = {
                'client_id': config.CLIENT_ID,
                'client_secret': config.CLIENT_SECRET,
                'refresh_token': athlete.refresh_token,
                'grant_type': 'refresh_token'
            }

            response = requests.post(
                url     = token_url,
                data    = request_body,
                timeout = 100,
                verify  = config.SSL_ENABLE
            )
            response.raise_for_status()  # Raises an HTTPError for bad responses
            token_data = response.json()
            self.update_token(athlete, token_data)

        return athlete.access_token if athlete else None
