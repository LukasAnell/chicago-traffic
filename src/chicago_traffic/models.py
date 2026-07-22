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


@dataclass
class CrashRecord:
    """Represents a crash record in the Chicago traffic dataset."""

    crash_record_id: str
    crash_date: datetime
    date_police_notified: datetime
    posted_speed_limit: int
    traffic_control_device: str
    device_condition: str
    weather_condition: str
    lightning_condition: str
    first_crash_type: str
    trafficway_type: str
    alignment: str
    roadway_surface_cond: str
    road_defect: str
    damage: str
    prim_contributory_cause: str
    sec_contributory_cause: str
    street_no: str
    street_direction: str
    street_name: str
    beat_of_occurrence: str
    num_units: int
    crash_month: int
    injuries: CrashInjuries
    location: CrashLocation | None
    crash_type: str | None
    most_severe_injury: str | None
    extra: dict[str, str]
