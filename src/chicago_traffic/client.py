import warnings
from datetime import datetime
from types import TracebackType
from typing import Callable, cast

from httpx import Client, HTTPError, Response

from chicago_traffic.models import TrafficAPIError, TrafficSegment


class TrafficClient:
    base_url: str = "https://data.cityofchicago.org/resource"
    dataset_id: str = "/n4j6-wkkf.json"

    # Socrata's max page size for requests
    page_size: int = 1_000

    app_token: str | None
    client: Client

    def __init__(self, app_token: str | None = None):
        self.app_token = app_token
        self.client = Client(base_url=self.base_url)

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

    def get_live_speeds(self) -> list[TrafficSegment]:
        # Declare empty json_response list to append each page of the response to
        json_response: list[dict[str, str | None]] = []

        try:
            offset: int = 0
            while True:
                response: Response = self.client.get(
                    self.dataset_id,
                    params={"$limit": self.page_size, "$offset": offset},
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

                if len(page_data) < self.page_size:
                    break

                offset += self.page_size

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
        #

        return []

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
