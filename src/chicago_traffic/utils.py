from typing import Callable

import httpx


def fetch_all_pages(
    client: httpx.Client,
    dataset: str,
    page_size: int,
    extra_params: dict[str, object] | None = None,
) -> list[dict[str, str | None]]:
    return list()


def parse_rows[T](
    rows: list[dict[str, str | None]],
    row_to_object: Callable[[dict[str, str | None]], T],
    label: str,
) -> list[T]:
    return list()
