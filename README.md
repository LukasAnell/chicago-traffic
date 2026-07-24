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

---

## Data Models

---

## Design Notes

---

## Project Status

---
