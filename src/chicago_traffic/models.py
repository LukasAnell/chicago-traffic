from dataclasses import dataclass
from datetime import datetime


@dataclass
class TrafficSegment:
    """Represents a traffic segment in the Chicago traffic dataset."""

    segment_id: int
    street: str
    direction: str
    from_street: str
    to_street: str
    length: float
    street_heading: str
    comments: str | None
    start_lon: float
    start_lat: float
    end_lon: float
    end_lat: float
    current_speed: float
    last_updated: datetime

    @property
    def has_data(self) -> bool:
        return self.current_speed != -1


class TrafficAPIError(Exception):
    """Custom exception for errors related to the Traffic API."""

    cause: Exception | None

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)

        self.cause = cause
