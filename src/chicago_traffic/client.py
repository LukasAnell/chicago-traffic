from httpx import Client

from chicago_traffic.models import TrafficSegment


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

    def get_live_speeds(self) -> list[TrafficSegment]:
        # get response from API at base_url
        response = self.client.get(self.dataset_id)

        # parse response into list of TrafficSegment objects

        # turn raw response into structured JSON
        json_response = response.json()

        # for each item in the JSON response, create a TrafficSegment object and add it to the list of segments
        segments = []
        for item in json_response:
            segment_id: int = item["segment_id"]
            street: str = item["street"]
            direction: str = item["_direction"]
            from_street: str = item["_fromst"]
            to_street: str = item["tost"]
            length: float = item["_length"]
            street_heading: str = item["_strheading"]
            start_lon: float = item["_comments"]
            start_lat: float = item["start_lon"]
            end_lon: float = item["_lif_lat"]
            end_lat: float = item["_lif_lon"]
            current_speed: float = item["_lit_lat"]
            last_updated: str = item["_traffic"]
            comments: str = item["_last_updt"]

        return list()
