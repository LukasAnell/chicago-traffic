# chicago-traffic

A Python package that is used to fetch traffic and crash data from the City of Chicago's public data portal, which uses the Socrata SODA API.
It is solely a data ingestion library, and can be used by other projects to build on top of it.
It does not perform any analysis, storage, or visualization itself.

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

Within project files where chicago-traffic is needed. It can be imported and used as follows.

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

The `TrafficClient` can be used to access the three datasets provided by the City of Chicago via the Socrata SODA API.
An optional `app_token` can be provided to raise the rate limit for Socrata API requests. No authentication is required for read access.

### `get_live_speeds() -> list[TrafficSegment]`

This function fetches the most recent traffic speeds for all monitored road segments in the city of Chicago (dataset `n4j6-wkkf`).

- Pagination of data is handled internally.
- Coverage varies by route because the speed data comes from CTA bus GPS traces rather than dedicated sensors. This means that only about 30% of segments will have a reading at any given time. Always check `segment.has_data` before querying `current_speed`.
    - A `current_speed` of `-1` indicates that the segment has no data at the time of the request.
- All timestamps in a single snapshot of the segments happen at roughly the same time, rather than being a rolling feed.
- The data only covers non-freeway, arterial streets.

### `get_historical_speeds(start: datetime, end: datetime | None = None, segment_ids: list[int] | None = None) -> list[TrafficSegment]`

Fetches historical traffic speeds for all monitored road segments in the city of Chicago (datasets `n4j6-wkkf` and `5c7e-3z7z`).
Because the historical data is split across two datasets, the library handles the routing of requests to the correct dataset based on the requested time range.

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

### `TrafficSegment`

One road-segment speed reading.
All fields are required except for `comments`, which seems to not be supplied very often.

| Field | Type | Notes |
|---|---|---|
| `segment_id` | `int` | |
| `street` | `str` | |
| `direction` | `str` | |
| `from_street` / `to_street` | `str` | |
| `length` | `float` | |
| `street_heading` | `str` | |
| `comments` | `str \| None` | Often `None`, and always `None` for historical data |
| `start_lon` / `start_lat` / `end_lon` / `end_lat` | `float` | |
| `current_speed` | `float` | `-1` indicates no data, but use `has_data`, rather than checking `-1` directly |
| `last_updated` | `datetime` | |
| `has_data` | `bool` (property) | `True` when `current_speed != -1` |

### `CrashRecord`

One crash report. Splits fields into core fields (which are always present), fields that may be useful (but are not always present), two nested objects (`CrashInjuries` and `CrashLocation`), and an `extra` dictionary for any other fields that may be present in the dataset.

| Field | Type | Notes |
|---|---|---|
| ~20 core fields | various | e.g. `crash_record_id: str`, `crash_date: datetime`, `posted_speed_limit`, `weather_condition`, `first_crash_type`, `street_name`, etc. |
| `crash_type` | `str \| None` | Promoted out of `extra` for typed access |
| `most_severe_injury` | `str \| None` | Promoted out of `extra` for typed access |
| `injuries` | `CrashInjuries` | Always present as a unit |
| `location` | `CrashLocation \| None` | Present/absent as a unit, and older records can lack it entirely |
| `extra` | `dict[str, str]` | Sparse/administrative fields (listed below) |

`extra` currently includes the fields: `report_type`, `hit_and_run_i`, `intersection_related_i`, `private_property_i`, `statements_taken_i`, `photos_taken_i`, `lane_cnt`, `idot_control_no`, `crash_date_est_i`, `dooring_i`, `work_zone_i`, `work_zone_type`, `workers_present_i`.
More fields may be added in the future. If you need typed access to any of these fields, you will need to parse them yourself.

### `CrashInjuries`

A nested object on every `CrashRecord`.
Contains seven `int` fields: `total`, `fatal`, `incapacitating`, `non_incapacitating`, `reported_not_evident`, `no_indication`, `unknown`.
Some of these fields are reported as float-strings in older records (e.g. `"1.0"`), but the package parses them correctly into ints.

### `CrashLocation`

A nested object that's present on some `CrashRecord`s.
Contains the fields `latitude` and `longitude` as `float`, and will be present or absent together (Never one or the other).

### `TrafficAPIError`

A custom exception type that's used for all failure modes across the three data-fetching functions, including network errors, HTTP errors, and API-level errors.
It also has an optional `cause: Exception | None` attribute that points to the underlying exception that caused the failure, if any.
It's recommended to catch this exception when calling any of the three data-fetching functions, rather than catching specific exceptions.

---

## Design Notes

- No built-in local storage of data as of now.
- Small differences in field names between the datasets are normalized behind the scenes.

---

## Project Status

This project is in its very early stages, and is just something I'm making for myself to use in other projects. It's not published to PyPI yet, so the API is subject to change until then.
