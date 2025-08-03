"""Effort Repository for managing Strava segment efforts in the database."""
from datetime import datetime

import requests

from app.database import get_db_session, retry_db_operation
from app.helpers import TimeSpan
from app.models.challenge import Challenge
from app.models.effort import Effort
from app.services.athlete import AthleteRepository
from app.services.challenge import ChallengeRepository
from config import config


class EffortRepository:
    """Repository for managing Effort records in the database."""

    def __init__(self):
        self.session = get_db_session()

    def add(self, activity_id: int, athlete_id: int) -> bool:
        """Add a new effort record for the given activity ID.

        Args:
            activity_id (int): The ID of the activity.
            athlete_id (int): The ID of the athlete.

        Returns:
            bool: True if the effort was added, False if it already exists or current challenge not among segment efforts.
        """

        # If there are already efforts for this activity, do not add again
        if self.get_efforts_by_activity_id(activity_id):
            return False

        # Check if any challenge is currently active
        if not (current_challenge := ChallengeRepository().get_current()):
            return False

        # Fetch activity data from Strava API
        athlete_repo = AthleteRepository()
        access_token = athlete_repo.get_access_token(athlete_id)
        response = requests.get(
            url     = f"{config.STRAVA_API_URL}/activities/{activity_id}?include_all_efforts=true",
            headers = {"Authorization": f"Bearer {access_token}"},
            timeout = 100,
            verify  = config.SSL_ENABLE)

        if not response.ok:
            return False

        activity_data = response.json()

        # Check if the activity has any segment efforts
        if not (segment_efforts := activity_data.get('segment_efforts')):
            return False

        # Check any segment effort belongs to the current challenge
        effort_saved = False
        effort_filter = EffortFilter(current_challenge)

        for effort_data in segment_efforts:
            if effort_filter(effort_data):
                self._save_effort(effort_data)
                effort_saved = True

        return effort_saved

    @retry_db_operation(max_retries=3, delay=1)
    def delete_efforts_by_activity_id(self, activity_id: int) -> int:
        """Remove all effort records related with given activity ID."""
        deleted_count = self.session.query(Effort).filter_by(activity_id=activity_id).delete()
        return deleted_count

    @retry_db_operation(max_retries=3, delay=1)
    def delete_efforts_by_athlete_id(self, athlete_id: int) -> int:
        """Remove all effort records related with given athlete ID."""
        deleted_count = self.session.query(Effort).filter_by(athlete_id=athlete_id).delete()
        return deleted_count

    @retry_db_operation(max_retries=3, delay=1)
    def get_efforts_by_activity_id(self, activity_id: int) -> list[Effort]:
        """Retrieve all efforts related to a specific activity ID."""
        return self.session.query(Effort).filter_by(activity_id=activity_id).all()

    @retry_db_operation(max_retries=3, delay=1)
    def get_efforts_by_segment_id_and_date(self, segment_id: int, start_date: datetime, end_date: datetime) -> list[Effort]:
        """Retrieve all efforts for a specific segment within a date range."""
        return self.session.query(Effort).filter(
            Effort.segment_id == segment_id,
            Effort.start_date >= start_date,
            Effort.start_date <= end_date
        ).all()

    @retry_db_operation(max_retries=3, delay=1)
    def _save_effort(self, data: dict) -> None:
        """Save a single effort record to the database."""

        effort = Effort(
            id=data.get('id'),
            activity_id=data.get('activity', {}).get('id'),
            athlete_id=data.get('athlete', {}).get('id'),
            segment_id=data.get('segment', {}).get('id'),
            start_date=data.get('start_date'),
            elapsed_time=data.get('elapsed_time', 0),
        )

        self.session.add(effort)


class EffortFilter:
    """Filter the effort based on given challange."""

    def __init__(self, challenge: Challenge):
        """Initialize with challenge."""
        self.challenge = challenge
        self._segment_ids = {challenge.climb_segment_id, challenge.sprint_segment_id}
        self._challenge_timespan = TimeSpan(
            start = challenge.start_date,  # type: ignore
            end   = challenge.end_date     # type: ignore
        )

    def __call__(self, effort_data: dict) -> bool:
        """Check if the effort matches the challenge filter criteria."""

        effort_segment_id: int | None = effort_data.get('segment', {}).get('id')
        effort_start_date: datetime | None = effort_data.get('start_date')

        if not effort_segment_id or effort_segment_id not in self._segment_ids:
            return False

        if not effort_start_date or effort_start_date not in self._challenge_timespan:
            return False

        return True
