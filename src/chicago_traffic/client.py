import warnings
from datetime import datetime
from types import TracebackType
from typing import Callable, cast

from httpx import Client, HTTPError, Response

from chicago_traffic.models import (
    CrashInjuries,
    CrashLocation,
    CrashRecord,
    TrafficAPIError,
    TrafficSegment,
)


class TrafficClient:
    __BASE_URL: str = "https://data.cityofchicago.org/resource"

    # dataset identifiers in Socrata
    __LIVE_DATASET: str = "/n4j6-wkkf.json"
    __HISTORICAL_2024_TO_NOW: str = "/4g9f-3jbs.json"
    __HISTORICAL_2018_TO_2023: str = "/sxs8-h27x.json"
    __CRASHES_DATASET: str = "/85ca-t3if.json"

    # end date of 2018-2023, start date of 2024-now
    __HISTORICAL_BOUNDARY = datetime(2024, 6, 11)

    # Socrata's max page size for requests
    __PAGE_SIZE: int = 1_000

    app_token: str | None
    client: Client

    def __init__(self, app_token: str | None = None):
        self.app_token = app_token
        self.client = Client(base_url=self.__BASE_URL)

        # if user supplied a token, use it in future HTTP requests
        if self.app_token is not None:
            self.client.headers["X-App-Token"] = self.app_token

    def __enter__(self):
        _ = self.client.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_value: Exception | None,
        traceback: TracebackType | None,
    ) -> None:
        _ = self.client.__exit__(exc_type, exc_value, traceback)

    def close(self) -> None:
        self.client.close()

    def get_crashes(
        self, start: datetime, end: datetime | None = None
    ) -> list[CrashRecord]:
        if end is None:
            end = datetime.now()

        if start >= end:
            raise ValueError("Start datetime must be before end datetime")

        if (end - start).days > 7:
            warnings.warn(
                "Fetching crash data for a date range longer than 7 days may result in a large number of API requests and slow performance. Consider providing a shorter date range.",
                category=RuntimeWarning,
            )

        where: str = (
            f"crash_date >= '{start.strftime('%Y-%m-%dT%H:%M:%S')}'"
            f" AND crash_date <= '{end.strftime('%Y-%m-%dT%H:%M:%S')}'"
        )

        try:
            offset: int = 0
            json_response: list[dict[str, str | None]] = []

            while True:
                response: Response = self.client.get(
                    self.__CRASHES_DATASET,
                    params={
                        "$limit": self.__PAGE_SIZE,
                        "$offset": offset,
                        "$where": where,
                    },
                )
                _ = response.raise_for_status()

                raw: object = cast(object, response.json())

                if not isinstance(raw, list):
                    raise TrafficAPIError("Unexpected Traffic API response format")

                page_data: list[dict[str, str | None]] = cast(
                    list[dict[str, str | None]], raw
                )

                if not page_data:
                    break

                json_response.extend(page_data)

                if len(page_data) < self.__PAGE_SIZE:
                    break

                offset += self.__PAGE_SIZE
        except HTTPError as e:
            raise TrafficAPIError("Failed to fetch data from Traffic API", cause=e)

        # for each item in the JSON response, create a CrashRecord object and add it to the list of crashes
        crashes: list[CrashRecord] = []
        for item in json_response:
            try:
                crash_record_id: str = self._get_required(item, "crash_record_id", str)
                crash_date: datetime = self._get_required(
                    item,
                    "crash_date",
                    lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f"),
                )
                date_police_notified: datetime = self._get_required(
                    item,
                    "date_police_notified",
                    lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f"),
                )
                posted_speed_limit: int = self._get_required(
                    item, "posted_speed_limit", int
                )
                traffic_control_device: str = self._get_required(
                    item, "traffic_control_device", str
                )
                device_condition: str = self._get_required(
                    item, "device_condition", str
                )
                weather_condition: str = self._get_required(
                    item, "weather_condition", str
                )
                lighting_condition: str = self._get_required(
                    item, "lighting_condition", str
                )
                first_crash_type: str = self._get_required(
                    item, "first_crash_type", str
                )
                trafficway_type: str = self._get_required(item, "trafficway_type", str)
                alignment: str = self._get_required(item, "alignment", str)
                roadway_surface_cond: str = self._get_required(
                    item, "roadway_surface_cond", str
                )
                road_defect: str = self._get_required(item, "road_defect", str)
                damage: str = self._get_required(item, "damage", str)
                prim_contributory_cause: str = self._get_required(
                    item, "prim_contributory_cause", str
                )
                sec_contributory_cause: str = self._get_required(
                    item, "sec_contributory_cause", str
                )
                street_no: int = self._get_required(item, "street_no", int)
                street_direction: str = self._get_required(
                    item, "street_direction", str
                )
                street_name: str = self._get_required(item, "street_name", str)
                beat_of_occurrence: int = self._get_required(
                    item, "beat_of_occurrence", int
                )
                num_units: int = self._get_required(item, "num_units", int)
                crash_month: int = self._get_required(item, "crash_month", int)
                crash_hour: int = self._get_required(item, "crash_hour", int)
                crash_day_of_week: int = self._get_required(
                    item, "crash_day_of_week", int
                )
                injuries: CrashInjuries = CrashInjuries(
                    total=self._get_required(
                        item, "injuries_total", lambda s: int(float(s))
                    ),
                    fatal=self._get_required(
                        item, "injuries_fatal", lambda s: int(float(s))
                    ),
                    incapacitating=self._get_required(
                        item, "injuries_incapacitating", lambda s: int(float(s))
                    ),
                    non_incapacitating=self._get_required(
                        item, "injuries_non_incapacitating", lambda s: int(float(s))
                    ),
                    reported_not_evident=self._get_required(
                        item, "injuries_reported_not_evident", lambda s: int(float(s))
                    ),
                    no_indication=self._get_required(
                        item, "injuries_no_indication", lambda s: int(float(s))
                    ),
                    unknown=self._get_required(
                        item, "injuries_unknown", lambda s: int(float(s))
                    ),
                )
                location: CrashLocation | None = (
                    CrashLocation(
                        latitude=self._get_required(item, "latitude", float),
                        longitude=self._get_required(item, "longitude", float),
                    )
                    if item.get("latitude") is not None
                    and item.get("longitude") is not None
                    else None
                )
                crash_type: str | None = item.get("crash_type")
                most_severe_injury: str | None = item.get("most_severe_injury")
                extra: dict[str, str] = {
                    k: v
                    for k, v in item.items()
                    if (v is not None)
                    and k
                    not in {
                        "crash_record_id",
                        "crash_date",
                        "date_police_notified",
                        "posted_speed_limit",
                        "traffic_control_device",
                        "device_condition",
                        "weather_condition",
                        "lighting_condition",
                        "first_crash_type",
                        "trafficway_type",
                        "alignment",
                        "roadway_surface_cond",
                        "road_defect",
                        "damage",
                        "prim_contributory_cause",
                        "sec_contributory_cause",
                        "street_no",
                        "street_direction",
                        "street_name",
                        "beat_of_occurrence",
                        "num_units",
                        "crash_month",
                        "crash_hour",
                        "crash_day_of_week",
                        "injuries_total",
                        "injuries_fatal",
                        "injuries_incapacitating",
                        "injuries_non_incapacitating",
                        "injuries_reported_not_evident",
                        "injuries_no_indication",
                        "injuries_unknown",
                        "latitude",
                        "longitude",
                        "crash_type",
                        "most_severe_injury",
                    }
                }

                crash_record: CrashRecord = CrashRecord(
                    crash_record_id,
                    crash_date,
                    date_police_notified,
                    posted_speed_limit,
                    traffic_control_device,
                    device_condition,
                    weather_condition,
                    lighting_condition,
                    first_crash_type,
                    trafficway_type,
                    alignment,
                    roadway_surface_cond,
                    road_defect,
                    damage,
                    prim_contributory_cause,
                    sec_contributory_cause,
                    street_no,
                    street_direction,
                    street_name,
                    beat_of_occurrence,
                    num_units,
                    crash_month,
                    crash_hour,
                    crash_day_of_week,
                    injuries,
                    location,
                    crash_type,
                    most_severe_injury,
                    extra,
                )

                crashes.append(crash_record)
            except TrafficAPIError as e:
                warnings.warn(
                    f"Skipping crash record due to error: {e}",
                    category=RuntimeWarning,
                )
                continue

        return crashes

    def get_live_speeds(self) -> list[TrafficSegment]:
        # Declare empty json_response list to append each page of the response to
        json_response: list[dict[str, str | None]] = []

        try:
            offset: int = 0
            while True:
                response: Response = self.client.get(
                    self.__LIVE_DATASET,
                    params={"$limit": self.__PAGE_SIZE, "$offset": offset},
                )
                _ = response.raise_for_status()

                # pyright complains about raw being of type Any, so I'm just casting to an object to suppress the warning.
                # There is no behavior change
                raw: object = cast(object, response.json())

                if not isinstance(raw, list):
                    raise TrafficAPIError("Unexpected Traffic API response format")

                # turn raw response into structured JSON
                page_data: list[dict[str, str | None]] = cast(
                    list[dict[str, str | None]], raw
                )

                if not page_data:
                    break

                json_response.extend(page_data)

                if len(page_data) < self.__PAGE_SIZE:
                    break

                offset += self.__PAGE_SIZE

        except HTTPError as e:
            raise TrafficAPIError("Failed to fetch data from Traffic API", cause=e)

        # for each item in the JSON response, create a TrafficSegment object and add it to the list of segments
        segments: list[TrafficSegment] = []
        for item in json_response:
            try:
                segment_id: int = self._get_required(item, "segmentid", int)
                street: str = self._get_required(item, "street", str)
                direction: str = self._get_required(item, "_direction", str)
                from_street: str = self._get_required(item, "_fromst", str)
                to_street: str = self._get_required(item, "_tost", str)
                length: float = self._get_required(item, "_length", float)
                street_heading: str = self._get_required(item, "_strheading", str)
                comments: str | None = item.get("_comments")
                start_lon: float = self._get_required(item, "start_lon", float)
                start_lat: float = self._get_required(item, "_lif_lat", float)
                end_lon: float = self._get_required(item, "_lit_lon", float)
                end_lat: float = self._get_required(item, "_lit_lat", float)
                current_speed: float = self._get_required(item, "_traffic", float)
                last_updated: datetime = self._get_required(
                    item,
                    "_last_updt",
                    lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f"),
                )

                segment: TrafficSegment = TrafficSegment(
                    segment_id,
                    street,
                    direction,
                    from_street,
                    to_street,
                    length,
                    street_heading,
                    comments,
                    start_lon,
                    start_lat,
                    end_lon,
                    end_lat,
                    current_speed,
                    last_updated,
                )

                segments.append(segment)
            except TrafficAPIError as e:
                warnings.warn(
                    f"Skipping segment due to error: {e}",
                    category=RuntimeWarning,
                )
                continue

        # return list of TrafficSegment objects
        return segments

    def get_historical_speeds(
        self,
        start: datetime,
        end: datetime | None = None,
        segment_ids: list[int] | None = None,
    ) -> list[TrafficSegment]:
        if end is None:
            end = datetime.now()

        if start >= end:
            raise ValueError("Start datetime must be before end datetime")

        # if no segment_ids is provided and the date range is more than 7 days, give the user a warning
        if segment_ids is None and (end - start).days > 7:
            warnings.warn(
                "Fetching historical speeds for a date range longer than 7 days may result in a large number of API requests and slow performance. Consider providing specific segment IDs or a shorter date range.",
                category=RuntimeWarning,
            )

        # historical datasets cover 2018-2023, and 2024-current
        datasets: list[str]
        if end < self.__HISTORICAL_BOUNDARY:
            datasets = [self.__HISTORICAL_2018_TO_2023]
        elif start >= self.__HISTORICAL_BOUNDARY:
            datasets = [self.__HISTORICAL_2024_TO_NOW]
        else:
            datasets = [self.__HISTORICAL_2018_TO_2023, self.__HISTORICAL_2024_TO_NOW]

        where: str = (
            f"time >= '{start.strftime('%Y-%m-%dT%H:%M:%S')}'"
            f" AND time <= '{end.strftime('%Y-%m-%dT%H:%M:%S')}'"
        )

        if segment_ids is not None:
            ids_list: str = ",".join(str(id) for id in segment_ids)
            where += f" AND segment_id IN ({ids_list})"

        json_response: list[dict[str, str | None]] = []

        for dataset in datasets:
            # fetch data for each dataset and combine results
            try:
                offset: int = 0

                while True:
                    response: Response = self.client.get(
                        dataset,
                        params={
                            "$limit": self.__PAGE_SIZE,
                            "$offset": offset,
                            "$where": where,
                        },
                    )
                    _ = response.raise_for_status()

                    raw: object = cast(object, response.json())

                    if not isinstance(raw, list):
                        raise TrafficAPIError("Unexpected Traffic API response format")

                    page_data: list[dict[str, str | None]] = cast(
                        list[dict[str, str | None]], raw
                    )

                    if not page_data:
                        break

                    json_response.extend(page_data)

                    if len(page_data) < self.__PAGE_SIZE:
                        break

                    offset += self.__PAGE_SIZE
            except HTTPError as e:
                raise TrafficAPIError(
                    f"Failed to fetch data from dataset {dataset}", cause=e
                )

        # both historical datasets use a different field naming convention than the live dataset
        # (no underscore prefixes and no comments field)
        segments: list[TrafficSegment] = []
        for item in json_response:
            try:
                segment_id: int = self._get_required(item, "segment_id", int)
                street: str = self._get_required(item, "street", str)
                direction: str = self._get_required(item, "direction", str)
                from_street: str = self._get_required(item, "from_street", str)
                to_street: str = self._get_required(item, "to_street", str)
                length: float = self._get_required(item, "length", float)
                street_heading: str = self._get_required(item, "street_heading", str)
                comments: str | None = item.get("comments")
                start_lon: float = self._get_required(item, "start_longitude", float)
                start_lat: float = self._get_required(item, "start_latitude", float)
                end_lon: float = self._get_required(item, "end_longitude", float)
                end_lat: float = self._get_required(item, "end_latitude", float)
                current_speed: float = self._get_required(item, "speed", float)
                last_updated: datetime = self._get_required(
                    item,
                    "time",
                    lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f"),
                )

                segment: TrafficSegment = TrafficSegment(
                    segment_id,
                    street,
                    direction,
                    from_street,
                    to_street,
                    length,
                    street_heading,
                    comments,
                    start_lon,
                    start_lat,
                    end_lon,
                    end_lat,
                    current_speed,
                    last_updated,
                )

                segments.append(segment)
            except TrafficAPIError as e:
                warnings.warn(
                    f"Skipping segment due to error: {e}",
                    category=RuntimeWarning,
                )
                continue

        return segments

    def _get_required[T](
        self, data: dict[str, str | None], key: str, convert: Callable[[str], T]
    ) -> T:
        value = data.get(key)

        if value is None:
            raise TrafficAPIError(
                f"Missing required field '{key}' in Traffic API response"
            )

        try:
            return convert(value)
        except Exception as e:
            raise TrafficAPIError(
                f"Failed to convert field '{key}' to the correct type", cause=e
            )
