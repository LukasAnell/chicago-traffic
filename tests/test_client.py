from typing import cast

import pytest
import respx
from httpx import Request, Response

from chicago_traffic.client import TrafficClient
from chicago_traffic.models import TrafficAPIError, TrafficSegment


def make_segment(segment_id: int = 1) -> dict[str, str | None]:
    """Helper function to create a mock traffic segment with default values."""
    return {
        "segmentid": str(segment_id),
        "street": "Cermak",
        "_direction": "EB",
        "_fromst": "California",
        "_tost": "Western",
        "_length": str(0.5),
        "_strheading": "W",
        "_comments": None,
        "start_lon": str(-87.6954340282),
        "_lif_lat": str(41.8517403632),
        "_lit_lon": str(-87.6856474998),
        "_lit_lat": str(41.8519327365),
        "_traffic": str(-1),
        "_last_updt": "2026-04-30 01:10:17.0",
    }


# Single page
def test_single_page():
    with respx.mock:
        _ = respx.get("https://data.cityofchicago.org/resource/n4j6-wkkf.json").mock(
            return_value=Response(
                200,
                json=[make_segment(i) for i in range(1, 6)],
            )
        )

        with TrafficClient() as client:
            segments: list[TrafficSegment] = client.get_live_speeds()

            assert len(respx.calls) == 1
            assert len(segments) == 5
            assert segments[0].street == "Cermak"
            assert segments[0].current_speed == -1.0


# Multi-page
def test_multi_page():
    with respx.mock:
        _ = respx.get("https://data.cityofchicago.org/resource/n4j6-wkkf.json").mock(
            side_effect=[
                Response(
                    200,
                    json=[make_segment(i) for i in range(1000)],
                ),
                Response(
                    200,
                    json=[make_segment(i) for i in range(250)],
                ),
            ]
        )

        with TrafficClient() as client:
            segments: list[TrafficSegment] = client.get_live_speeds()

            assert len(respx.calls) == 2
            assert len(segments) == 1250


# Exact multiple
def test_exact_multiple():
    with respx.mock:
        _ = respx.get("https://data.cityofchicago.org/resource/n4j6-wkkf.json").mock(
            side_effect=[
                Response(
                    200,
                    json=[make_segment(i) for i in range(1000)],
                ),
                Response(
                    200,
                    json=[],
                ),
            ]
        )

        with TrafficClient() as client:
            segments: list[TrafficSegment] = client.get_live_speeds()

            assert len(respx.calls) == 2
            assert len(segments) == 1000


# Empty dataset
def test_empty_dataset():
    with respx.mock:
        _ = respx.get("https://data.cityofchicago.org/resource/n4j6-wkkf.json").mock(
            return_value=Response(
                200,
                json=[],
            )
        )

        with TrafficClient() as client:
            segments: list[TrafficSegment] = client.get_live_speeds()

            assert len(respx.calls) == 1
            assert segments == []


# HTTP error on first page
def test_http_error_first_page():
    with respx.mock:
        _ = respx.get("https://data.cityofchicago.org/resource/n4j6-wkkf.json").mock(
            return_value=Response(
                500,
            )
        )

        # uses pytest.raises to make sure that TrafficAPIError is raised when the request returns a 500 error
        with TrafficClient() as client:
            with pytest.raises(TrafficAPIError):
                _ = client.get_live_speeds()


# HTTP error mid-pagination
def test_http_error_mid_pagination():
    with respx.mock:
        _ = respx.get("https://data.cityofchicago.org/resource/n4j6-wkkf.json").mock(
            side_effect=[
                Response(
                    200,
                    json=[make_segment(i) for i in range(1000)],
                ),
                Response(
                    500,
                ),
            ]
        )

        with TrafficClient() as client:
            with pytest.raises(TrafficAPIError):
                _ = client.get_live_speeds()


# Malformed row on page 2
def test_malformed_row_skipped_with_warning():
    with respx.mock:
        _ = respx.get("https://data.cityofchicago.org/resource/n4j6-wkkf.json").mock(
            side_effect=[
                Response(
                    200,
                    json=[make_segment(i) for i in range(1000)],
                ),
                Response(
                    200,
                    json=[{"malformed": "row"}],
                ),
            ]
        )

        with TrafficClient() as client:
            with pytest.warns(RuntimeWarning):
                _ = client.get_live_speeds()


# Correct $offset values sent
def test_correct_offset():
    with respx.mock:
        _ = respx.get("https://data.cityofchicago.org/resource/n4j6-wkkf.json").mock(
            side_effect=[
                Response(
                    200,
                    json=[make_segment(i) for i in range(1000)],
                ),
                Response(
                    200,
                    json=[make_segment(i) for i in range(250)],
                ),
            ]
        )

        with TrafficClient() as client:
            _ = client.get_live_speeds()

            request: Request = cast(Request, respx.calls[0].request)
            assert request.url.params["$offset"] == "0"
            assert request.url.params["$limit"] == "1000"

            request = cast(Request, respx.calls[1].request)
            assert request.url.params["$offset"] == "1000"
            assert request.url.params["$limit"] == "1000"


# has_data property
def test_has_data_true():
    # segment with current_speed != -1, so has_data is True
    segment: dict[str, str | None] = make_segment()
    segment["_traffic"] = str(25.0)

    with respx.mock:
        _ = respx.get("https://data.cityofchicago.org/resource/n4j6-wkkf.json").mock(
            return_value=Response(
                200,
                json=[segment],
            )
        )

        with TrafficClient() as client:
            segments: list[TrafficSegment] = client.get_live_speeds()

            assert len(respx.calls) == 1
            assert len(segments) == 1
            assert segments[0].current_speed == 25.0
            assert segments[0].has_data is True


def test_has_data_false():
    # segment with current_speed == -1, so has_data is False
    segment: dict[str, str | None] = make_segment()
    segment["_traffic"] = str(-1.0)

    with respx.mock:
        _ = respx.get("https://data.cityofchicago.org/resource/n4j6-wkkf.json").mock(
            return_value=Response(
                200,
                json=[segment],
            )
        )

        with TrafficClient() as client:
            segments: list[TrafficSegment] = client.get_live_speeds()

            assert len(respx.calls) == 1
            assert len(segments) == 1
            assert segments[0].current_speed == -1.0
            assert segments[0].has_data is False
