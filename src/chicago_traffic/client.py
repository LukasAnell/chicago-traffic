from httpx import Client


class TrafficClient:
    base_url: str = "https://data.cityofchicago.org/resource/n4j6-wkkf.json"

    app_token: str | None
    session: Client

    def __init__(self, app_token: str | None = None):
        self.app_token = app_token
        self.session = Client(base_url=self.base_url)

        # if user supplied a token, use it in future HTTP requests
        if self.app_token is not None:
            self.session.headers["X-App-Token"] = self.app_token
