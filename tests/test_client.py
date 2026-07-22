import warnings
from datetime import datetime
from typing import cast

import pytest
import respx
from httpx import Request, Response

from chicago_traffic.client import TrafficClient
from chicago_traffic.models import TrafficAPIError, TrafficSegment

HISTORICAL_2018_TO_2023_URL = "https://data.cityofchicago.org/resource/sxs8-h27x.json"
HISTORICAL_2024_TO_NOW_URL = "https://data.cityofchicago.org/resource/kf7e-cur8.json"


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


# Range is fully before the boundary so only the 2018-2023 dataset is queried
def test_historical_routes_to_legacy_dataset_only():
    with respx.mock:
        legacy_route = respx.get(HISTORICAL_2018_TO_2023_URL).mock(
            return_value=Response(200, json=[make_segment(i) for i in range(1, 4)])
        )
        current_route = respx.get(HISTORICAL_2024_TO_NOW_URL).mock(
            return_value=Response(200, json=[])
        )

        with TrafficClient() as client:
            segments: list[TrafficSegment] = client.get_historical_speeds(
                start=datetime(2019, 1, 1),
                end=datetime(2019, 1, 2),
            )

            assert legacy_route.called
            assert not current_route.called
            assert len(segments) == 3


# Range after the boundary, only the 2024-now dataset is queried
def test_historical_routes_to_current_dataset_only():
    with respx.mock:
        legacy_route = respx.get(HISTORICAL_2018_TO_2023_URL).mock(
            return_value=Response(200, json=[])
        )
        current_route = respx.get(HISTORICAL_2024_TO_NOW_URL).mock(
            return_value=Response(200, json=[make_segment(i) for i in range(1, 4)])
        )

        with TrafficClient() as client:
            segments: list[TrafficSegment] = client.get_historical_speeds(
                start=datetime(2025, 1, 1),
                end=datetime(2025, 1, 2),
            )

            assert not legacy_route.called
            assert current_route.called
            assert len(segments) == 3


# Range goes over the 2023-2024 foundary, so both datasets are queried and results combine
def test_historical_boundary_queries_both_datasets():
    with respx.mock:
        legacy_route = respx.get(HISTORICAL_2018_TO_2023_URL).mock(
            return_value=Response(200, json=[make_segment(i) for i in range(1, 3)])
        )
        current_route = respx.get(HISTORICAL_2024_TO_NOW_URL).mock(
            return_value=Response(200, json=[make_segment(i) for i in range(3, 7)])
        )

        with TrafficClient() as client:
            segments: list[TrafficSegment] = client.get_historical_speeds(
                start=datetime(2024, 1, 1),
                end=datetime(2024, 12, 1),
            )

            assert legacy_route.called
            assert current_route.called
            assert len(segments) == 6


# $where clause contains correctly formatted start/end bounds
def test_historical_where_clause_date_bounds():
    with respx.mock:
        route = respx.get(HISTORICAL_2018_TO_2023_URL).mock(
            return_value=Response(200, json=[])
        )

        with TrafficClient() as client:
            _ = client.get_historical_speeds(
                start=datetime(2019, 3, 1, 8, 30, 0),
                end=datetime(2019, 3, 2, 9, 0, 0),
            )

            request: Request = cast(Request, route.calls[0].request)
            where = request.url.params["$where"]
            assert "_last_updt >= '2019-03-01T08:30:00'" in where
            assert "_last_updt <= '2019-03-02T09:00:00'" in where
            assert "segmentid IN" not in where


# $where clause includes segmentid IN(...) when segment_ids is provided
def test_historical_where_clause_segment_ids():
    with respx.mock:
        route = respx.get(HISTORICAL_2018_TO_2023_URL).mock(
            return_value=Response(200, json=[])
        )

        with TrafficClient() as client:
            _ = client.get_historical_speeds(
                start=datetime(2019, 3, 1),
                end=datetime(2019, 3, 2),
                segment_ids=[101, 202, 303],
            )

            request: Request = cast(Request, route.calls[0].request)
            where = request.url.params["$where"]
            assert "segmentid IN (101,202,303)" in where


# Range > 7 days with no segment_ids gives a RuntimeWarning
def test_historical_warns_on_long_range_without_segment_ids():
    with respx.mock:
        _ = respx.get(HISTORICAL_2018_TO_2023_URL).mock(
            return_value=Response(200, json=[])
        )

        with TrafficClient() as client:
            with pytest.warns(RuntimeWarning):
                _ = client.get_historical_speeds(
                    start=datetime(2019, 1, 1),
                    end=datetime(2019, 2, 1),
                )


# Range > 7 days but segment_ids provided doesn't give a warning
def test_historical_no_warning_when_segment_ids_provided():
    with respx.mock:
        _ = respx.get(HISTORICAL_2018_TO_2023_URL).mock(
            return_value=Response(200, json=[])
        )

        with TrafficClient() as client:
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                _ = client.get_historical_speeds(
                    start=datetime(2019, 1, 1),
                    end=datetime(2019, 2, 1),
                    segment_ids=[101],
                )


# Range <= 7 days with no segment_ids, no warning
def test_historical_no_warning_when_range_short():
    with respx.mock:
        _ = respx.get(HISTORICAL_2018_TO_2023_URL).mock(
            return_value=Response(200, json=[])
        )

        with TrafficClient() as client:
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                _ = client.get_historical_speeds(
                    start=datetime(2019, 1, 1),
                    end=datetime(2019, 1, 3),
                )


# start >= end raises ValueError before any request is made
def test_historical_start_after_end_raises_value_error():
    with respx.mock:
        route = respx.get(HISTORICAL_2018_TO_2023_URL).mock(
            return_value=Response(200, json=[])
        )

        with TrafficClient() as client:
            with pytest.raises(ValueError):
                _ = client.get_historical_speeds(
                    start=datetime(2019, 1, 2),
                    end=datetime(2019, 1, 1),
                )

            assert not route.called


def test_historical_start_equal_end_raises_value_error():
    with respx.mock:
        with TrafficClient() as client:
            with pytest.raises(ValueError):
                same = datetime(2019, 1, 1)
                _ = client.get_historical_speeds(start=same, end=same)


# end defaults to "now" when not specified
def test_historical_end_defaults_to_now():
    with respx.mock:
        route = respx.get(HISTORICAL_2024_TO_NOW_URL).mock(
            return_value=Response(200, json=[])
        )

        with TrafficClient() as client:
            before = datetime.now()
            _ = client.get_historical_speeds(start=datetime(2026, 1, 1))
            after = datetime.now()

            request: Request = cast(Request, route.calls[0].request)
            where = request.url.params["$where"]

            # extract the end bound and check it falls within [before, after]
            end_str = where.split("<= '")[1].split("'")[0]
            end_value = datetime.strptime(end_str, "%Y-%m-%dT%H:%M:%S")
            assert before.replace(microsecond=0) <= end_value <= after


# HTTP error on the only dataset in range throws a TrafficAPIError, with no partial data
def test_historical_http_error_single_dataset():
    with respx.mock:
        _ = respx.get(HISTORICAL_2018_TO_2023_URL).mock(return_value=Response(500))

        with TrafficClient() as client:
            with pytest.raises(TrafficAPIError):
                _ = client.get_historical_speeds(
                    start=datetime(2019, 1, 1),
                    end=datetime(2019, 1, 2),
                )


# HTTP error on the second dataset when straddling throws TrafficAPIError, no partial data
def test_historical_http_error_second_dataset_no_partial_results():
    with respx.mock:
        _ = respx.get(HISTORICAL_2018_TO_2023_URL).mock(
            return_value=Response(200, json=[make_segment(i) for i in range(1, 4)])
        )
        _ = respx.get(HISTORICAL_2024_TO_NOW_URL).mock(return_value=Response(500))

        with TrafficClient() as client:
            with pytest.raises(TrafficAPIError):
                _ = client.get_historical_speeds(
                    start=datetime(2024, 1, 1),
                    end=datetime(2024, 12, 1),
                )


# HTTP error mid-pagination within a single dataset
def test_historical_http_error_mid_pagination():
    with respx.mock:
        _ = respx.get(HISTORICAL_2018_TO_2023_URL).mock(
            side_effect=[
                Response(200, json=[make_segment(i) for i in range(1000)]),
                Response(500),
            ]
        )

        with TrafficClient() as client:
            with pytest.raises(TrafficAPIError):
                _ = client.get_historical_speeds(
                    start=datetime(2019, 1, 1),
                    end=datetime(2019, 6, 1),
                    segment_ids=[1],
                )


# Pagination within a single historical dataset
def test_historical_pagination_within_one_dataset():
    with respx.mock:
        _ = respx.get(HISTORICAL_2018_TO_2023_URL).mock(
            side_effect=[
                Response(200, json=[make_segment(i) for i in range(1000)]),
                Response(200, json=[make_segment(i) for i in range(250)]),
            ]
        )

        with TrafficClient() as client:
            segments: list[TrafficSegment] = client.get_historical_speeds(
                start=datetime(2019, 1, 1),
                end=datetime(2019, 6, 1),
                segment_ids=[1],
            )

            assert len(segments) == 1250


# Offset resets to 0 for each dataset when the data range goes over the boundary
def test_historical_offset_resets_per_dataset():
    with respx.mock:
        legacy_route = respx.get(HISTORICAL_2018_TO_2023_URL).mock(
            side_effect=[
                Response(200, json=[make_segment(i) for i in range(1000)]),
                Response(200, json=[make_segment(i) for i in range(50)]),
            ]
        )
        current_route = respx.get(HISTORICAL_2024_TO_NOW_URL).mock(
            return_value=Response(200, json=[make_segment(i) for i in range(10)])
        )

        with TrafficClient() as client:
            _ = client.get_historical_speeds(
                start=datetime(2024, 1, 1),
                end=datetime(2024, 12, 1),
            )

            legacy_first = cast(Request, legacy_route.calls[0].request)
            legacy_second = cast(Request, legacy_route.calls[1].request)
            current_first = cast(Request, current_route.calls[0].request)

            assert legacy_first.url.params["$offset"] == "0"
            assert legacy_second.url.params["$offset"] == "1000"
            assert current_first.url.params["$offset"] == "0"
