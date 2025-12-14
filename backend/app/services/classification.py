"""Classification Service for retrieving the general classification of athletes over a season."""
from typing import Any, Generator

from app.database import get_db_session, retry_db_operation
from app.helpers import Gender, TimeSpan
from app.models.athlete import Athlete
from app.models.challenge import Challenge
from app.models.effort import Effort
from app.services.results import ResultService
from config import Config


class ClassificationResults:
    """Class for handling classification results for a specific athlete."""

    def __init__(self, athlete_id: int):
        self.athlete_id = athlete_id

        self._completed_sprints : list[tuple[int, int]] = []  # List like (challenge_id, points)
        self._completed_climbs  : list[tuple[int, int]] = []  # List like (challenge_id, points)

    def add_result(self, challenge_id: int, segment_type: str, points: int) -> None:
        """Add a result for the athlete.

        Args:
            segment_type (str): The type of segment ("sprint" or "climb").
            points (int): The points earned in the segment.
        """
        if segment_type == "sprint":
            self._completed_sprints.append((challenge_id, points))

        elif segment_type == "climb":
            self._completed_climbs.append((challenge_id, points))

        else:
            raise ValueError(f"Invalid segment type: {segment_type}")

    @property
    def sprint_points(self) -> int:
        """Get total sprint points.

        Only the top N results are counted, where N is defined in Config.MAX_COUNTED_RESULTS.
        """
        self._completed_sprints.sort(key=lambda x: x[1], reverse=True)
        return sum(points for _, points in self._completed_sprints[:Config.MAX_COUNTED_RESULTS])

    @property
    def climb_points(self) -> int:
        """Get total climb points.

        Only the top N results are counted, where N is defined in Config.MAX_COUNTED_RESULTS.
        """
        self._completed_climbs.sort(key=lambda x: x[1], reverse=True)
        return sum(points for _, points in self._completed_climbs[:Config.MAX_COUNTED_RESULTS])

    @property
    def completed_sprints_count(self) -> int:
        """Get count of completed sprints."""
        return len(self._completed_sprints)

    @property
    def completed_climbs_count(self) -> int:
        """Get count of completed climbs."""
        return len(self._completed_climbs)

    @property
    def counted_sprints_count(self) -> int:
        """Get count of counted sprints."""
        return min(len(self._completed_sprints), Config.MAX_COUNTED_RESULTS)

    @property
    def counted_climbs_count(self) -> int:
        """Get count of counted climbs."""
        return min(len(self._completed_climbs), Config.MAX_COUNTED_RESULTS)


class ClassificationService:
    """Service to generate general classification for the whole season"""

    def __init__(self, season_time_span: TimeSpan):
        """Initialize ClassificationService with a ResultService instance."""
        self.season_time_span: TimeSpan                        = season_time_span
        self.efforts         : list[Effort]                    = []   # List of efforts within the season time span
        self.athletes        : list[tuple[int, str, str, str]] = []   # List of tuples (athlete_id, firstname, lastname, sex)
        self.challenges      : list[Challenge]                 = []   # Challenges within the season time span

        self._results : dict[int, ClassificationResults] = {}  # Maps athlete_id to classification results for that athlete

    @retry_db_operation(max_retries=3, delay=1)
    def query_from_db(self) -> None:
        """Query the database to populate the service with efforts, athletes, and challenges."""
        session = get_db_session()
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
            self._results[athlete[0]] = ClassificationResults(athlete[0])

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

            result_service = ResultService(challenge.id)    # type: ignore
            result_service.populate(
                climb_segment_id  = climb_segment,          # type: ignore
                sprint_segment_id = sprint_segment,         # type: ignore
                efforts           = challenge_efforts,
                athletes          = list(filter(lambda a: a[0] in challenge_athletes, self.athletes))   # pylint: disable=cell-var-from-loop
            )

            for segment_type in challenge_types:
                for result_data in result_service.yield_simplified_results(segment_type, gender):
                    athlete_id = result_data[0]

                    if not athlete_id in self._results:
                        self._results[athlete_id] = ClassificationResults(athlete_id)

                    self._results[athlete_id].add_result(challenge.id, segment_type, result_data[2])

        athlete_names = self.athlete_names
        athlete_genders = self.athlete_genders

        for athlete in self.athletes:
            if athlete[3] != gender:
                continue
            ath_id = athlete[0]
            results = self._results.get(ath_id, ClassificationResults(ath_id))

            yield {
                "athlete_id": ath_id,
                "athlete_name": athlete_names[ath_id],
                "gender": athlete_genders[ath_id],
                "total_sprint_points": results.sprint_points,
                "total_climb_points": results.climb_points,
                "completed_sprints": results.completed_sprints_count,
                "completed_climbs": results.completed_climbs_count,
                "counted_sprints": results.counted_sprints_count,
                "counted_climbs": results.counted_climbs_count
            }
