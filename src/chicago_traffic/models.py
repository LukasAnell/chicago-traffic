from dataclasses import dataclass


@dataclass
class TrafficSegment:
    """Represents a traffic segment in the Chicago traffic dataset."""

    segment_id: int | None
    street: str | None
    direction: str | None
    from_street: str | None
    to_street: str | None
    current_speed: float | None
    last_updated: str | None
    start_lon: float | None
    start_lat: float | None
    end_lon: float | None
    end_lat: float | None

    def __init__(
        self,
        segment_id: int | None,
        street: str | None,
        direction: str | None,
        from_street: str | None,
        to_street: str | None,
        current_speed: float | None,
        last_updated: str | None,
        start_lon: float | None,
        start_lat: float | None,
        end_lon: float | None,
        end_lat: float | None,
    ):
        self.segment_id = segment_id
        self.street = street
        self.direction = direction
        self.from_street = from_street
        self.to_street = to_street
        self.current_speed = current_speed
        self.last_updated = last_updated
        self.start_lon = start_lon
        self.start_lat = start_lat
        self.end_lon = end_lon
        self.end_lat = end_lat
