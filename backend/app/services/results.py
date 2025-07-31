from typing import Any, Generator, Iterable

from app.helpers import Gender
from app.models.athlete import Athlete
from app.models.challenge import Challenge
from app.models.effort import Effort
from config import config
from sqlalchemy.orm import Session


class ResultService:
    """Service to handle results for a specific challenge."""
    points: list[int] = config.POINTS

    def __init__(self):
        """Initialize ResultService"""
        self._segment_ids: dict[str, int] = {}
        self._challenge_efforts: list[Effort] = []
        self._challenge_id: int = 0
        self._participating_athletes: list[tuple[int, str, str, str]] = []

    def populate(self, *,
                 challenge_id: int,
                 climb_segment_id: int,
                 sprint_segment_id: int,
                 efforts: list[Effort],
                 athletes: list[tuple[int, str, str, str]]) -> None:
        """Populate ResultService manually with data.

        Use this method, when data is already available and you want to avoid querying the database.

        Args:
            challenge_id (int): The ID of the challenge.
            climb_segment_id (int): The ID of the climb segment.
            sprint_segment_id (int): The ID of the sprint segment.
            efforts (list[Effort]): List of Effort objects for the challenge.
            athletes (list[tuple[int, str, str, str]]): List of tuples containing
                athlete ID, first name, last name, and gender.
        """
        self._challenge_id = challenge_id
        self._segment_ids = {
            "climb": climb_segment_id,
            "sprint": sprint_segment_id
        }
        self._challenge_efforts = efforts
        self._participating_athletes = athletes

    def query_from_db(self, challenge_id: int, session: Session) -> None:
        """Query the database to populate the service for a specific challenge ID

        This makes 3 queries to the database:
        1. Get the challenge by ID.
        2. Get all efforts for the challenge's segments within the time span.
        3. Get all athletes who have participated in the challenge.

        Args:
            challenge_id (int): The ID of the challenge to get results for.
            session (Session): SQLAlchemy session for database operations.

        Raises:
            ValueError: If the challenge is not found.
        """
        # Get segment IDs for the challenge
        challenge = (
            session.query(Challenge)
            .filter_by(id=challenge_id)
            .first()
        )
        if not challenge:
            raise ValueError("Challenge not found")

        self._segment_ids = {                   # type: ignore
            "climb": challenge.climb_segment_id,
            "sprint": challenge.sprint_segment_id
        }

        self._challenge_efforts = session.query(Effort).filter(
            Effort.segment_id.in_(self._segment_ids.values()),
            Effort.start_date >= challenge.start_date,
            Effort.start_date <= challenge.end_date
        ).all()

        self._participating_athletes = session.query(           # type: ignore
            Athlete.id, Athlete.firstname, Athlete.lastname, Athlete.sex
        ).filter(
            Athlete.id.in_({effort.athlete_id for effort in self._challenge_efforts})
        ).all()

    @property
    def athlete_names(self) -> dict[int, str]:
        """Get a dictionary mapping athlete IDs to their full names."""
        return {athlete[0]: f"{athlete[1]} {athlete[2]}" for athlete in self._participating_athletes}

    @property
    def athlete_genders(self) -> dict[int, Gender]:
        """Get a dictionary mapping athlete IDs to their genders."""
        return {athlete[0]: Gender(athlete[3]) for athlete in self._participating_athletes}

    @staticmethod
    def _filter_best_efforts(efforts: Iterable[Effort]) -> list[Effort]:
        """Filter the best efforts for each athlete and segment combination.

        This method ensures that for each athlete and segment, only the effort with the lowest elapsed time is kept.
        It also sorts the results by elapsed time in ascending order.

        Args:
            efforts (list[Effort]): List of Effort objects to filter.

        Returns:
            list[Effort]: List of filtered Effort objects with the best efforts for each athlete-segment combination.
        """
        # Remove duplicates, keeping only the effort with the lowest time for each athlete-segment combination
        best_efforts: dict[tuple[int, int], Effort] = {}
        for effort in efforts:
            key = (effort.athlete_id, effort.segment_id)
            if key not in best_efforts or effort.elapsed_time < best_efforts[key].elapsed_time:  # type: ignore
                best_efforts[key] = effort  # type: ignore

        return sorted(best_efforts.values(), key=lambda e: e.elapsed_time)  # type: ignore

    def yield_results(self, segment_type: str, gender: Gender) -> Generator[dict[str, Any], None, None]:
        """Get results for a specific segment and gender."""
        if segment_type not in self._segment_ids:
            raise ValueError("Invalid segment type. Must be 'climb' or 'sprint'.")

        if gender not in Gender.values():
            raise ValueError(f"Invalid gender: {gender}. Must be {' or '.join(Gender.values())}.")

        efforts_filter = ResultFilter(gender, segment_type, self)
        relevant_efforts = filter(efforts_filter, self._challenge_efforts)

        for i, effort in enumerate(self._filter_best_efforts(relevant_efforts)):
            result_dict = {
                "id": effort.id,
                "athlete_id": effort.athlete_id,
                "athlete_name": self.athlete_names.get(effort.athlete_id, "Unknown"),  # type: ignore
                "challenge_id": self._challenge_id,
                "segment_id": effort.segment_id,
                "segment_type": segment_type,
                "time": effort.elapsed_time,
                "recorded_at": effort.start_date.isoformat(),
                "points": self.points[i] if i < len(self.points) else 0,
                "position": i + 1
            }
            yield result_dict


class ResultFilter:
    """Filter results based on gender and segment id."""

    def __init__(self, gender: Gender, segment_type: str, result_service: ResultService):
        """Initialize ResultFilter with gender and segment id."""
        if gender not in Gender.values():
            raise ValueError(f"Invalid gender: {gender}. Must be {' or '.join(Gender.values())}.")

        self.gender = gender
        self._segment_id = result_service._segment_ids[segment_type]
        self.athlete_genders = result_service.athlete_genders

    def __call__(self, effort: Effort) -> bool:
        """Check if the effort matches the filter criteria."""
        if self._segment_id != effort.segment_id:   # type: ignore
            return False

        if not (gender := self.athlete_genders.get(effort.athlete_id)) or gender != self.gender:  # type: ignore
            return False

        return True
