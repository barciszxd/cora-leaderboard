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

    def __lt__(self, other: datetime) -> bool:
        """Check if this time span ends before another timestamp."""
        if not isinstance(other, datetime):
            raise NotImplementedError
        return self.end < other

    def __gt__(self, other: datetime) -> bool:
        """Check if this time span starts after another timestamp."""
        if not isinstance(other, datetime):
            raise NotImplementedError
        return self.start > other

    def __le__(self, other: datetime) -> bool:
        """Check if this time span ends before or at another timestamp."""
        if not isinstance(other, datetime):
            raise NotImplementedError
        return self.end <= other

    def __ge__(self, other: datetime) -> bool:
        """Check if this time span starts after or at another timestamp."""
        if not isinstance(other, datetime):
            raise NotImplementedError
        return self.start >= other


class Gender(enum.StrEnum):
    """Enumeration for gender."""
    MALE = "M"
    FEMALE = "F"

    @classmethod
    def values(cls) -> list[str]:
        """Return a list of all gender values."""
        return [cls.MALE, cls.FEMALE]
