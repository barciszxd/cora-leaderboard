"""Challenge Repository Module"""
from datetime import datetime, timezone

from app.models.challenge import Challenge
from app.services.segment import SegmentRepository
from sqlalchemy.orm import Session


class ChallengeRepository:
    """Repository for managing Challenge records in the database."""

    def __init__(self, session: Session):
        self.session = session

    def add(self,
            name: str,
            climb_segment_id: int,
            sprint_segment_id: int,
            start_date: datetime,
            end_date: datetime) -> Challenge:
        """Add a new challenge."""
        challenge = Challenge(
            name              = name,
            climb_segment_id  = climb_segment_id,
            sprint_segment_id = sprint_segment_id,
            start_date        = start_date,
            end_date          = end_date
        )
        self.session.add(challenge)

        segment_repo = SegmentRepository(self.session)
        segment_repo.create(climb_segment_id)
        segment_repo.create(sprint_segment_id)

        return challenge

    def delete_by_id(self, challenge_id: int) -> bool:
        """Delete challenge by ID."""
        challenge = self.get_by_id(challenge_id)
        if challenge:
            self.session.delete(challenge)
            return True
        return False

    def get_by_id(self, challenge_id: int) -> Challenge | None:
        """Get challenge by ID."""
        return self.session.query(Challenge).filter_by(id=challenge_id).first()

    def get_current(self) -> Challenge | None:
        """Get current active challenge.

        Returns the challenge where current time is between start_time and end_time.

        Returns:
            Challenge | None: The current active challenge if found, otherwise None.
        """
        current_time = datetime.now(timezone.utc)

        return self.session.query(Challenge).filter(
            Challenge.start_date <= current_time,
            Challenge.end_date >= current_time
        ).first()

    def get_all(self) -> list[Challenge]:
        """Get all challenges."""
        return self.session.query(Challenge).all()
