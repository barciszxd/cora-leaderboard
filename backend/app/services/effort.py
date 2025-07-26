import requests

from app.models.effort import Effort
from app.services.athlete import AthleteRepository
from app.services.challenge import ChallengeRepository
from config import config
from sqlalchemy.orm import Session


class EffortRepository:
    """Repository for managing Effort records in the database."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, activity_id: int, athlete_id: int) -> bool:
        """Add a new effort record for the given activity ID.

        Args:
            activity_id (int): The ID of the activity.
            athlete_id (int): The ID of the athlete.

        Returns:
            bool: True if the effort was added, False if it already exists or current challenge not among segment efforts.
        """

        existing_efforts = self.get_efforts_by_activity_id(activity_id)

        if existing_efforts:
            return False

        # Check if any challenge is currently active
        challenge_repo = ChallengeRepository(self.session)
        if not (current_challenge := challenge_repo.get_current()):
            return False

        # Fetch activity data from Strava API
        athlete_repo = AthleteRepository(self.session)
        access_token = athlete_repo.get_access_token(athlete_id)
        response = requests.get(
            url     = f"{config.STRAVA_API_URL}/activities/{activity_id}?include_all_efforts=true",
            headers = {"Authorization": f"Bearer {access_token}"},
            timeout = 100,
            verify  = config.SSL_ENABLE)
        response.raise_for_status()
        activity_data = response.json()

        # Check if the current challenge segment is among the segment efforts of the activity
        if not (segment_efforts := activity_data.get('segment_efforts')):
            return False

        effort_saved = False

        for effort in segment_efforts:
            if effort.get('segment', {}).get('id') == current_challenge.segment_id:
                self._save_effort(effort)
                effort_saved = True

        return effort_saved

    def delete_efforts_by_activity_id(self, activity_id: int) -> bool:
        """Remove all effort records related with given activity ID."""
        efforts_to_remove = self.session.query(Effort).filter_by(activity_id=activity_id).all()

        if efforts_to_remove:
            for effort in efforts_to_remove:
                self.session.delete(effort)
            return True

        return False

    def delete_efforts_by_athlete_id(self, athlete_id: int) -> bool:
        """Remove all effort records related with given athlete ID."""
        efforts_to_remove = self.session.query(Effort).filter_by(athlete_id=athlete_id).all()

        if efforts_to_remove:
            for effort in efforts_to_remove:
                self.session.delete(effort)
            return True

        return False

    def get_efforts_by_activity_id(self, activity_id: int) -> list[Effort]:
        """Retrieve all efforts related to a specific activity ID."""
        return self.session.query(Effort).filter_by(activity_id=activity_id).all()

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
