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

        #

        return list()
