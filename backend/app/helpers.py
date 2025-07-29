"""Module with various helper functions and classes."""
import enum

from datetime import datetime


class TimeSpan:
    """Class to represent a time span with start and end timestamps."""

    def __init__(self, start: datetime, end: datetime):
        """Initialize the TimeSpan with start and end timestamps."""
        self.start = start
        self.end = end

    def __contains__(self, timestamp: datetime) -> bool:
        """Check if a timestamp is within the time span."""
        return self.start <= timestamp <= self.end


class Gender(enum.StrEnum):
    """Enumeration for gender."""
    MALE = "M"
    FEMALE = "F"

    @classmethod
    def values(cls) -> list[str]:
        """Return a list of all gender values."""
        return [cls.MALE, cls.FEMALE]
