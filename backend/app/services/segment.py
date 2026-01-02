import requests

from app.database import get_db_session, retry_db_operation
from app.models.challenge import Challenge
from app.models.segment import Segment
from app.services.athlete import AthleteRepository
from config import config


class SegmentRepository:
    """Repository for managing Segment records in the database."""

    def __init__(self):
        self.session = get_db_session()

    def create(self, segment_id: int) -> Segment | None:
        """Add a new segment record for the given segment data from STRAVA API.

        Args:
            segment_data (dict): The segment data from STRAVA API.

        Returns:
            bool: True if the segment was added, False if it already exists or current challenge not among segment efforts.
        """
        if existing_segment := self.get_by_id(segment_id):
            return existing_segment

        segment_data = self._request_segment_details(segment_id)

        if not segment_data:
            return None

        return self._save_segment(segment_data)

    @retry_db_operation(max_retries=3, delay=1)
    def get_by_id(self, segment_id: int) -> Segment | None:
        """Get segment by ID."""
        return self.session.query(Segment).filter_by(id=segment_id).first()

    def get_for_challenge(self, challenge: Challenge) -> tuple[Segment | None, Segment | None]:
        """Get segment details for a challenge."""

        climb_segment = self.get_by_id(challenge.climb_segment_id)  # type: ignore
        sprint_segment = self.get_by_id(challenge.sprint_segment_id)  # type: ignore

        return sprint_segment, climb_segment

    def _request_segment_details(self, segment_id: int) -> dict | None:
        """Get segment details from STRAVA."""

        athlete_repo = AthleteRepository()
        access_token = athlete_repo.get_access_token(17596625)  # TODO: Replace with admin athlete ID

        response = requests.get(
            url     = f"{config.STRAVA_API_URL}/segments/{segment_id}",
            headers = {"Authorization": f"Bearer {access_token}"},
            timeout = 100,
            verify  = config.SSL_ENABLE)

        if not response.ok:
            return None

        return response.json()

    @retry_db_operation(max_retries=3, delay=1)
    def _save_segment(self, segment_data: dict) -> Segment:
        """Save segment data to the database."""

        # Strava API bug: old segments may not have total_elevation_gain field; calculate it if missing
        if (elevation_gain := segment_data.get('total_elevation_gain')) == 0.0:
            elevation_gain = segment_data.get('elevation_high', 0) - segment_data.get('elevation_low', 0)
            elevation_gain = round(max(elevation_gain, 0), 2)

        # Create and save the Segment object
        segment = Segment(
            id             = segment_data.get('id'),
            name           = segment_data.get('name', 'Unknown Segment'),
            distance       = segment_data.get('distance', 0),
            elevation_gain = elevation_gain
        )
        self.session.add(segment)
        return segment

    @staticmethod
    def to_dict(segment: Segment) -> dict:
        """Convert a Segment object to a dictionary."""
        return {
            "id": segment.id,
            "name": segment.name,
            "distance": segment.distance,
            "elevation_gain": segment.elevation_gain
        }
