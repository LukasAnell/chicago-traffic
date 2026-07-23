from datetime import datetime

from chicago_traffic.models import (
    CrashInjuries,
    CrashLocation,
    CrashRecord,
    TrafficAPIError,
    TrafficSegment,
)


def make_segment(current_speed: float = 25.0) -> TrafficSegment:
    """Helper to build a minimal TrafficSegment for model-level tests."""
    return TrafficSegment(
        segment_id=1,
        street="Cermak",
        direction="EB",
        from_street="California",
        to_street="Western",
        length=0.5,
        street_heading="W",
        comments=None,
        start_lon=-87.6954340282,
        start_lat=41.8517403632,
        end_lon=-87.6856474998,
        end_lat=41.8519327365,
        current_speed=current_speed,
        last_updated=datetime(2026, 4, 30, 1, 10, 17),
    )


def make_crash_record(
    location: CrashLocation | None = None,
    crash_type: str | None = "NO INJURY / DRIVE AWAY",
    most_severe_injury: str | None = "NO INDICATION OF INJURY",
    extra: dict[str, str] | None = None,
) -> CrashRecord:
    """Helper to build a minimal CrashRecord for model-level tests."""
    return CrashRecord(
        crash_record_id="abc123",
        crash_date=datetime(2026, 4, 30, 14, 22, 0),
        date_police_notified=datetime(2026, 4, 30, 15, 0, 0),
        posted_speed_limit=30,
        traffic_control_device="TRAFFIC SIGNAL",
        device_condition="FUNCTIONING PROPERLY",
        weather_condition="CLEAR",
        lighting_condition="DAYLIGHT",
        first_crash_type="REAR END",
        trafficway_type="ONE-WAY",
        alignment="STRAIGHT AND LEVEL",
        roadway_surface_cond="DRY",
        road_defect="NO DEFECTS",
        damage="$500 OR LESS",
        prim_contributory_cause="FOLLOWING TOO CLOSELY",
        sec_contributory_cause="UNABLE TO DETERMINE",
        street_no=6220,
        street_direction="W",
        street_name="CERMAK RD",
        beat_of_occurrence=331,
        num_units=2,
        crash_month=4,
        crash_hour=14,
        crash_day_of_week=5,
        injuries=CrashInjuries(
            total=0,
            fatal=0,
            incapacitating=0,
            non_incapacitating=0,
            reported_not_evident=0,
            no_indication=2,
            unknown=0,
        ),
        location=location,
        crash_type=crash_type,
        most_severe_injury=most_severe_injury,
        extra=extra if extra is not None else {},
    )


def test_has_data_true_for_normal_speed():
    segment = make_segment(current_speed=25.0)
    assert segment.has_data is True


def test_has_data_false_for_sentinel_value():
    # -1 signals that there was no data
    segment = make_segment(current_speed=-1)
    assert segment.has_data is False


def test_has_data_true_for_zero_speed():
    # 0 doesn't signify no data
    segment = make_segment(current_speed=0)
    assert segment.has_data is True


def test_traffic_api_error_message():
    err = TrafficAPIError("something went wrong")
    assert str(err) == "something went wrong"
    assert err.cause is None


def test_traffic_api_error_with_cause():
    original = ValueError("bad value")
    err = TrafficAPIError("wrapped error", cause=original)
    assert err.cause is original
    assert isinstance(err.cause, ValueError)


def test_traffic_api_error_is_exception():
    assert issubclass(TrafficAPIError, Exception)


def test_crash_injuries_construction():
    injuries = CrashInjuries(
        total=3,
        fatal=1,
        incapacitating=1,
        non_incapacitating=1,
        reported_not_evident=0,
        no_indication=0,
        unknown=0,
    )
    assert injuries.total == 3
    assert injuries.fatal == 1


def test_crash_location_construction():
    location = CrashLocation(latitude=41.85, longitude=-87.69)
    assert location.latitude == 41.85
    assert location.longitude == -87.69


def test_crash_record_construction_with_location():
    record = make_crash_record(location=CrashLocation(41.85, -87.69))
    assert record.crash_record_id == "abc123"
    assert record.location is not None
    assert record.location.latitude == 41.85
    assert record.injuries.no_indication == 2


def test_crash_record_construction_without_location():
    record = make_crash_record(location=None)
    assert record.location is None


def test_crash_record_optional_severity_fields_can_be_none():
    record = make_crash_record(crash_type=None, most_severe_injury=None)
    assert record.crash_type is None
    assert record.most_severe_injury is None


def test_crash_record_extra_defaults_and_holds_arbitrary_fields():
    record = make_crash_record(extra={"hit_and_run_i": "Y", "lane_cnt": "2"})
    assert record.extra["hit_and_run_i"] == "Y"
    assert record.extra["lane_cnt"] == "2"
    assert "crash_record_id" not in record.extra


def test_crash_record_extra_empty_by_default():
    record = make_crash_record()
    assert record.extra == {}
