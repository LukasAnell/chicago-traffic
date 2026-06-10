import httpx
import respx

from chicago_traffic.client import TrafficClient


def make_segment(segment_id: int = 1) -> dict[str, str | None]:
    """Helper function to create a mock traffic segment with default values."""
    return {
        "segment_id": str(segment_id),
        "street": "Cermak",
        "direction": "EB",
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
            return_value=httpx.Response(
                200,
                json=[make_segment(i) for i in range(1, 6)],
            )
        )

        with TrafficClient() as client:
            segments = client.get_live_speeds()
            assert len(segments) == 5


# Multi-page


# Exact multiple


# Empty dataset


# HTTP error mid-pagination


# Malformed row on page 2


# Correct $offset values sent
