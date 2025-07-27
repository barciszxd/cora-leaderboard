import requests

from app.models.segment import Segment
from app.services.athlete import AthleteRepository
from config import config
from sqlalchemy.orm import Session


class SegmentRepository:
    """Repository for managing Segment records in the database."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, segment_id: int) -> Segment | None:
        """Add a new segment record for the given segment data from STRAVA API.

        Args:
            segment_data (dict): The segment data from STRAVA API.

        Returns:
            bool: True if the segment was added, False if it already exists or current challenge not among segment efforts.
        """
        if existing_segment := self.session.query(Segment).filter_by(id=segment_id).first():
            return existing_segment

        segment_data = self._get_segment_details(segment_id)

        if not segment_data:
            return None

        segment = Segment(
            id             = segment_id,
            name           = segment_data.get('name'),
            distance       = segment_data.get('distance'),
            elevation_gain = segment_data.get('total_elevation_gain')
        )
        self.session.add(segment)

        return segment

    def get_by_id(self, segment_id: int) -> Segment | None:
        """Get segment by ID."""
        return self.session.query(Segment).filter_by(id=segment_id).first()

    # get segment details from Strava API
    def _get_segment_details(self, segment_id: int) -> dict | None:
        """Get segment details from Strava API."""

        athlete_repo = AthleteRepository(self.session)
        access_token = athlete_repo.get_access_token(17596625)  # TODO: Replace with admin athlete ID

        response = requests.get(
            url     = f"{config.STRAVA_API_URL}/segments/{segment_id}",
            headers = {"Authorization": f"Bearer {access_token}"},
            timeout = 100,
            verify  = config.SSL_ENABLE)
        response.raise_for_status()
        return response.json()
