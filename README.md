# chicago-traffic

A Python package that is used to fetch traffic and crash data from the City of Chicago's public data portal, which uses the Socrata SODA API. It is solely a data ingestion library, and can be used by other projects to build on top of it. It does not perform any analysis, storage, or visualization itself.

---

## Requirements

- Python >= 3.14
- [httpx](https://www.python-httpx.org/)

---

## Installation

Currently not published to PyPI, so it must be installed locally as an editable dependency.

```bash
uv pip install -e /path/to/chicago-traffic
```

---

## Example Usage

Within project files where chicago-traffic is needed: it can be imported and used as follows.

```python
from chicago_traffic import TrafficClient
from datetime import datetime

# The app_token field is optional, but can be used to get higher rate limits from the Socrata API.
client = TrafficClient()

# As of now, ~1,257 arterial segments are tracked, with current speeds updated every ~10 minutes.
segments = client.get_live_speeds()
for s in segments:
    if s.has_data:
        print(s.street, s.current_speed)

# Historical speeds can also be fetched, and the library will transparently span the 2018-2023 and 2024-now datasets.
history = client.get_historical_speeds(
    start=datetime(2026, 1, 1),
    end=datetime(2026, 1, 8),
)

## Crash records since September 2017 can also be fetched.
crashes = client.get_crashes(
    start=datetime(2026, 1, 1),
    end=datetime(2026, 1, 8),
)

client.close()
```

`TrafficClient` can also be used as a context manager:

```python
with TrafficClient() as client:
    segments = client.get_live_speeds()
```    

---

## API

### `TrafficClient(app_token: str | None = None)`

The `TrafficClient` can be used to access the three datasets provided by the City of Chicago via the Socrata SODA API. An optional `app_token` can be provided to raise the rate limit for Socrata API requests. No authentication is required for read access.

### `get_live_speeds() -> list[TrafficSegment]`

This function fetches the most recent traffic speeds for all monitored road segments in the city of Chicago (dataset `n4j6-wkkf`).

- Pagination of data is handled internally.
- Coverage varies by route because the speed data comes from CTA bus GPS traces rather than dedicated sensors. This means that only about 30% of segments will have a reading at any given time. Always check `segment.has_data` before querying `current_speed`.
    - A `current_speed` of `-1` indicates that the segment has no data at the time of the request.
- All timestamps in a single snapshot of the segments happen at roughly the same time, rather than being a rolling feed.
- The data only covers non-freeway, arterial streets.

### `get_historical_speeds(start: datetime, end: datetime | None = None, segment_ids: list[int] | None = None) -> list[TrafficSegment]`

Fetches historical traffic speeds for all monitored road segments in the city of Chicago (datasets `n4j6-wkkf` and `5c7e-3z7z`). Because the historical data is split across two datasets, the library handles the routing of requests to the correct dataset based on the requested time range.

- `end` defaults to the current time if not provided.
- A list of `segment_ids` can be provided to filter the results to only those segments. If not provided, all segments will be returned.
- Raises a `RuntimeWarning` if the requested time range exceeds 7 days and no `segment_ids` are provided.
- If either of the datasets fails to return data, the function will raise a `TrafficAPIError` and return no results.
- The historical data seems to lag behind the live data by a bit (I haven't determined exactly how long, or if it's the same each time).

### `get_crashes(start: datetime, end: datetime | None = None) -> list[CrashRecord]`

Fetches crash records (dataset `85ca-t3if`, spanning from September 2017-present) for the city of Chicago.

- `end` defaults to the current time if not provided.
- Raises a `RuntimeWarning` if the requested time range exceeds 7 days.
- There's no way to filter the results by street-name, severity, or geographic area, the function will return all crashes in the city for the requested time range.

---

## Data Models

---

## Design Notes

---

## Project Status

---
