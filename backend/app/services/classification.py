from typing import Any, Generator

from app.helpers import Gender, TimeSpan
from app.models.athlete import Athlete
from app.models.challenge import Challenge
from app.models.effort import Effort
from app.services.results import ResultService
from sqlalchemy.orm import Session


class ClassificationService:
    """Service to generate general classification for the whole season"""

    def __init__(self, season_time_span: TimeSpan):
        """Initialize ClassificationService with a ResultService instance."""
        self.season_time_span = season_time_span
        self.efforts: list[Effort] = []
        self.athletes: list[tuple[int, str, str, str]] = []
        self.challenges: list[Challenge] = []
        self.total_points: dict[int, list[int]] = {}  # Maps athlete_id to [climb_points, sprint_points]

    def query_from_db(self, session: Session) -> None:
        """Query the database to populate the service with efforts, athletes, and challenges."""
        # Get all challenges within the season time span
        self.challenges = session.query(Challenge).filter(
            Challenge.start_date >= self.season_time_span.start,
            Challenge.end_date <= self.season_time_span.end
        ).all()

        if not self.challenges:
            return

        self.efforts = session.query(Effort).filter(
            Effort.start_date >= self.season_time_span.start,
            Effort.start_date <= self.season_time_span.end
        ).all()

        if not self.efforts:
            return

        self.athletes = session.query(           # type: ignore
            Athlete.id, Athlete.firstname, Athlete.lastname, Athlete.sex
        ).filter(
            Athlete.id.in_({effort.athlete_id for effort in self.efforts})
        ).all()

        for athlete in self.athletes:
            self.total_points[athlete[0]] = [0, 0]

    @property
    def athlete_names(self) -> dict[int, str]:
        """Get a dictionary mapping athlete IDs to their full names."""
        return {athlete[0]: f"{athlete[1]} {athlete[2]}" for athlete in self.athletes}

    @property
    def athlete_genders(self) -> dict[int, str]:
        """Get a dictionary mapping athlete IDs to their genders."""
        return {athlete[0]: athlete[3] for athlete in self.athletes}

    def yield_classification(self, gender: Gender) -> Generator[dict[str, Any], None, None]:
        """Yield classification results for each challenge."""
        challenge_types = ["sprint", "climb"]

        for challenge in self.challenges:
            climb_segment = challenge.climb_segment_id
            sprint_segment = challenge.sprint_segment_id

            challenge_efforts = [
                effort for effort in self.efforts
                if effort.segment_id in (climb_segment, sprint_segment) and     # type: ignore
                challenge.start_date <= effort.start_date <= challenge.end_date
            ]
            challenge_athletes = {effort.athlete_id for effort in challenge_efforts}

            result_service = ResultService()
            result_service.populate(
                challenge_id      = challenge.id,           # type: ignore
                climb_segment_id  = climb_segment,          # type: ignore
                sprint_segment_id = sprint_segment,         # type: ignore
                efforts           = challenge_efforts,
                athletes          = list(filter(lambda a: a[0] in challenge_athletes, self.athletes))
            )

            for segment_type in challenge_types:
                for result in result_service.yield_simplified_results(segment_type, gender):
                    athlete_id = result[0]

                    self.total_points[athlete_id][challenge_types.index(segment_type)] += result[2]

        athlete_names = self.athlete_names
        athlete_genders = self.athlete_genders

        for athlete in self.athletes:
            if athlete[3] != gender:
                continue
            ath_id = athlete[0]
            yield {
                "athlete_id": ath_id,
                "athlete_name": athlete_names[ath_id],
                "gender": athlete_genders[ath_id],
                "total_sprint_points": self.total_points[ath_id][0],
                "total_climb_points": self.total_points[ath_id][1],
            }
