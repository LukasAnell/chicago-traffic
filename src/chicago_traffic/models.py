from dataclasses import dataclass


@dataclass
class TrafficSegment:
    """Represents a traffic segment in the Chicago traffic dataset."""

    segment_id: str | None
    street: str | None
    direction: str | None
    from_street: str | None
    to_street: str | None
    length: str | None
    street_heading: str | None
    comments: str | None
    start_lon: str | None
    start_lat: str | None
    end_lon: str | None
    end_lat: str | None
    current_speed: str | None
    last_updated: str | None

    def __init__(
        self,
        segment_id: str | None,
        street: str | None,
        direction: str | None,
        from_street: str | None,
        to_street: str | None,
        length: str | None,
        street_heading: str | None,
        comments: str | None,
        start_lon: str | None,
        start_lat: str | None,
        end_lon: str | None,
        end_lat: str | None,
        current_speed: str | None,
        last_updated: str | None,
    ):
        self.segment_id = segment_id
        self.street = street
        self.direction = direction
        self.from_street = from_street
        self.to_street = to_street
        self.length = length
        self.street_heading = street_heading
        self.comments = comments
        self.start_lon = start_lon
        self.start_lat = start_lat
        self.end_lon = end_lon
        self.end_lat = end_lat
        self.current_speed = current_speed
        self.last_updated = last_updated


class TrafficAPIError(Exception):
    """Custom exception for errors related to the Traffic API."""

    def __init__(self, message: str):
        super().__init__(message)
