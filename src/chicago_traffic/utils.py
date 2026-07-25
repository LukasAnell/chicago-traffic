import warnings
from typing import Callable, cast

import httpx

from chicago_traffic.models import TrafficAPIError


def fetch_all_pages(
    client: httpx.Client,
    dataset: str,
    page_size: int,
    extra_params: dict[str, str | int] | None = None,
) -> list[dict[str, str | None]]:
    offset = 0
    json_response: list[dict[str, str | None]] = []

    try:
        while True:
            params: dict[str, str | int] = {"$limit": page_size, "$offset": offset}
            if extra_params is not None:
                params.update(extra_params)

            response: httpx.Response = client.get(dataset, params=params)
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

            if len(page_data) < page_size:
                break

            offset += page_size
    except httpx.HTTPError as e:
        raise TrafficAPIError(f"Failed to fetch data from dataset {dataset}", cause=e)

    return json_response


def parse_rows[T](
    rows: list[dict[str, str | None]],
    row_to_object: Callable[[dict[str, str | None]], T],
    label: str,
) -> list[T]:
    results: list[T] = []

    for item in rows:
        try:
            results.append(row_to_object(item))
        except TrafficAPIError as e:
            warnings.warn(
                f"Skipping {label} due to error: {e}", category=RuntimeWarning
            )
            continue

    return results
