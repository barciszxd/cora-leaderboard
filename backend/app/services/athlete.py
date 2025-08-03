"""Athlete Repository Module"""
import logging

from datetime import datetime, timezone

import requests

from app.database import get_db_session, retry_db_operation
from app.models.athlete import Athlete
from config import config

logger = logging.getLogger(__name__)


class AthleteRepository:
    """Repository for managing Athlete records in the database."""

    def __init__(self):
        self.session = get_db_session()

    def create(self, athlete_data: dict, token_data: dict) -> Athlete:
        """Create a new athlete."""
        # Check if athlete already exists
        athlete = self.get_by_id(athlete_data['id'])
        if athlete:
            return athlete

        return self._save_athlete(athlete_data, token_data)

    def update(self, athlete: Athlete, athlete_data: dict, token_data: dict) -> Athlete | None:
        """Update an existing athlete."""
        athlete.firstname     = athlete_data.get('firstname', athlete.firstname)
        athlete.lastname      = athlete_data.get('lastname', athlete.lastname)
        athlete.sex           = athlete_data.get('sex', athlete.sex)
        athlete.access_token  = token_data.get('access_token', athlete.access_token)
        athlete.refresh_token = token_data.get('refresh_token', athlete.refresh_token)
        athlete.expires_at    = token_data.get('expires_at', athlete.expires_at)

        return athlete

    @retry_db_operation(max_retries=3, delay=1)
    def delete_by_id(self, athlete_id: int) -> bool:
        """Delete athlete by ID."""
        deleted_count = self.session.query(Athlete).filter_by(id=athlete_id).delete()
        return deleted_count > 0

    def update_token(self, athlete: Athlete, token_data: dict) -> Athlete:
        """Update the access token for an athlete."""
        athlete.access_token  = token_data.get('access_token', athlete.access_token)
        athlete.refresh_token = token_data.get('refresh_token', athlete.refresh_token)
        athlete.expires_at    = token_data.get('expires_at', athlete.expires_at)

        return athlete

    @retry_db_operation(max_retries=3, delay=1)
    def get_by_id(self, athlete_id: int) -> Athlete | None:
        """Get athlete by ID."""
        return self.session.query(Athlete).filter_by(id=athlete_id).first()

    @retry_db_operation(max_retries=3, delay=1)
    def get_all(self) -> list[Athlete]:
        """Get all athletes."""
        return self.session.query(Athlete).all()

    def get_access_token(self, athlete_id: int) -> str | None:
        """Get access token for an athlete

        If the token is expired, get a new one from STRAVA and update the athlete record.

        Args:
            athlete_id (int): The ID of the athlete.

        Returns:
            str | None: The access token if available, otherwise None.
        """
        athlete = self.get_by_id(athlete_id)

        if not athlete:
            return None

        if athlete.expires_at < datetime.now(timezone.utc).timestamp():  # type: ignore
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

            if not response.ok:
                logger.error("Failed to refresh token for athlete %d: %s", athlete_id, response.text)
                return None

            token_data = response.json()
            self.update_token(athlete, token_data)

        return athlete.access_token  # type: ignore

    @retry_db_operation(max_retries=3, delay=1)
    def _save_athlete(self, athlete_data, token_data):
        athlete = Athlete(
            id            = athlete_data['id'],
            firstname     = athlete_data.get('firstname'),
            lastname      = athlete_data.get('lastname'),
            sex           = athlete_data.get('sex'),
            access_token  = token_data.get('access_token'),
            refresh_token = token_data.get('refresh_token'),
            expires_at    = token_data.get('expires_at'),
            token_type    = token_data.get('token_type', 'Bearer')
        )
        self.session.add(athlete)
        return athlete
