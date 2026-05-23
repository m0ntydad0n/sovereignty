from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load_schema(name: str) -> dict:
    with (SCHEMAS / name).open() as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return schema


def validate(name: str, instance: dict) -> None:
    Draft202012Validator(load_schema(name)).validate(instance)


def valid_lane_health() -> dict:
    return {
        "schema_version": "0.1",
        "lane": "hermes.local_router.coder",
        "status": "healthy",
        "checked_at": "2026-05-23T12:00:00Z",
        "latency_ms": 123,
        "last_success_at": "2026-05-23T11:59:59Z",
        "concurrency_limit": 2,
    }


def test_valid_lane_health_schema_passes():
    validate("lane-health.schema.json", valid_lane_health())


@pytest.mark.parametrize("status", ["degraded", "cooldown", "unavailable"])
def test_lane_health_schema_accepts_operational_statuses(status: str):
    record = {**valid_lane_health(), "status": status}
    if status == "cooldown":
        record["cooldown_until"] = "2026-05-23T12:05:00Z"
    if status != "healthy":
        record["last_failure_class"] = "TimeoutError"

    validate("lane-health.schema.json", record)


def test_lane_health_schema_rejects_invalid_status():
    record = {**valid_lane_health(), "status": "perfect"}

    with pytest.raises(ValidationError, match="perfect"):
        validate("lane-health.schema.json", record)


def test_lane_health_python_api_round_trips_schema_valid_dict():
    from sovereignty import LaneHealth

    record = LaneHealth.from_dict(valid_lane_health())

    assert record.to_dict() == valid_lane_health()
    validate("lane-health.schema.json", record.to_dict())
