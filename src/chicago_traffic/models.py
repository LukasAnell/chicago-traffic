from dataclasses import dataclass


@dataclass
class TrafficSegment:
    """Represents a traffic segment in the Chicago traffic dataset."""

    segment_id: int | None
    street: str | None
    direction: str | None
    from_street: str | None
    to_street: str | None
    length: float | None
    street_heading: str | None
    comments: str | None
    start_lon: float | None
    start_lat: float | None
    end_lon: float | None
    end_lat: float | None
    current_speed: float | None
    last_updated: str | None


class TrafficAPIError(Exception):
    """Custom exception for errors related to the Traffic API."""

    cause: Exception | None

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)

        self.cause = cause
