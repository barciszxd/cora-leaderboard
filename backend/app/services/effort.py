import requests

from app.models.effort import Efforts
from app.services.athlete import AthleteRepository
from app.services.challenge import ChallengeRepository
from config import config
from sqlalchemy.orm import Session


class EffortRepository:
    """Repository for managing Effort records in the database."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, activity_id: int, athlete_id: int) -> bool:
        """Add a new effort record for the given activity ID."""

        endpoint = f"{config.STRAVA_API_URL}/activities/{activity_id}?include_all_efforts=true"
        athlete_repo = AthleteRepository(self.session)
        challenge_repo = ChallengeRepository(self.session)
        access_token = athlete_repo.get_access_token(athlete_id)
        response = requests.get(endpoint, headers={"Authorization": f"Bearer {access_token}"}, timeout=100, verify=config.SSL_ENABLE)
        response.raise_for_status()
        data = response.json()

        if not (segment_efforts := data.get('segment_efforts')):
            return False

        current_challenge = challenge_repo.get_current()

        if not current_challenge:
            return False

        for effort in segment_efforts:
            if effort.get('segment', {}).get('id') == current_challenge.segment_id:
                self._save_effort(effort)
                return True

        return False

    def delete_efforts_by_activity_id(self, activity_id: int) -> bool:
        """Remove all effort records related with given activity ID."""
        efforts_to_remove = self.session.query(Efforts).filter_by(activity_id=activity_id).all()

        if efforts_to_remove:
            for effort in efforts_to_remove:
                self.session.delete(effort)
            return True

        return False

    def delete_efforts_by_athlete_id(self, athlete_id: int) -> bool:
        """Remove all effort records related with given athlete ID."""
        efforts_to_remove = self.session.query(Efforts).filter_by(athlete_id=athlete_id).all()

        if efforts_to_remove:
            for effort in efforts_to_remove:
                self.session.delete(effort)
            return True

        return False

    def _save_effort(self, data: dict) -> None:
        """Save a single effort record to the database."""

        effort = Efforts(
            id=data.get('id'),
            activity_id=data.get('activity', {}).get('id'),
            athlete_id=data.get('athlete', {}).get('id'),
            segment_id=data.get('segment', {}).get('id'),
            start_date=data.get('start_date'),
            elapsed_time=data.get('elapsed_time', 0),
        )

        self.session.add(effort)
