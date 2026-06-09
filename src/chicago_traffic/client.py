class TrafficClient:
    app_token: str | None

    def __init__(self, app_token: str | None = None):
        self.app_token = app_token
