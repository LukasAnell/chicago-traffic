from datetime import datetime
from types import TracebackType
from typing import cast

from httpx import Client, HTTPError

from chicago_traffic.models import TrafficAPIError, TrafficSegment


class TrafficClient:
    base_url: str = "https://data.cityofchicago.org/resource"
    dataset_id: str = "/n4j6-wkkf.json"

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

    def get_live_speeds(self) -> list[TrafficSegment]:
        try:
            # get response from API at base_url
            response = self.client.get(self.dataset_id)
            _ = response.raise_for_status()
        except HTTPError as e:
            raise TrafficAPIError("Failed to fetch data from Traffic API", cause=e)

        # turn raw response into structured JSON
        json_response: list[dict[str, str]] = cast(
            list[dict[str, str]], response.json()
        )

        try:
            # for each item in the JSON response, create a TrafficSegment object and add it to the list of segments
            segments: list[TrafficSegment] = []
            for item in json_response:
                segment_id: int = int(item["segment_id"])
                street: str = item["street"]
                direction: str = item["_direction"]
                from_street: str = item["_fromst"]
                to_street: str = item["_tost"]
                length: float = float(item["_length"])
                street_heading: str = item["_strheading"]
                comments: str | None = item.get("_comments")
                start_lon: float = float(item["start_lon"])
                start_lat: float = float(item["_lif_lat"])
                end_lon: float = float(item["_lit_lon"])
                end_lat: float = float(item["_lit_lat"])
                current_speed: float = float(item["_traffic"])
                last_updated: datetime = datetime.strptime(
                    item["_last_updt"], "%Y-%m-%d %H:%M:%S.%f"
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
        except (KeyError, ValueError) as e:
            raise TrafficAPIError("Failed to parse Traffic API response", cause=e)

        # return list of TrafficSegment objects
        return segments
