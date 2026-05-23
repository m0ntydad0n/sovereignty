from __future__ import annotations

import json
import re
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


def valid_packet_telemetry() -> dict:
    return {
        "schema_version": "0.1",
        "run_id": "run_1",
        "packet_id": "pkt_1",
        "trace_id": "trace_1",
        "adapter": "hermes-local-router",
        "lane": "writer",
        "action": "draft",
        "status": "success",
        "status_fields": {
            "local_lane_status": "success",
            "guardrail_status": "not_run",
            "exposure_status": "measured",
            "side_effect_status": "proposed_none",
        },
        "timing": {
            "started_at": "2026-05-23T12:00:00Z",
            "ended_at": "2026-05-23T12:00:01Z",
            "duration_ms": 1000,
        },
        "token_accounting": {
            "raw_input_tokens_estimated": 1200,
            "local_output_tokens_estimated": 120,
            "exposed_to_cloud_tokens_estimated": 180,
            "kept_local_tokens_estimated": 1020,
        },
        "privacy": {
            "metadata_only": True,
            "raw_payload_logged": False,
            "local_output_logged": False,
        },
    }


def test_valid_packet_telemetry_schema_accepts_metadata_only_record():
    validate("packet-telemetry.schema.json", valid_packet_telemetry())


@pytest.mark.parametrize("field", [
    "messages",
    "response",
    "prompt",
    "completion",
    "stdout",
    "stderr",
    "raw_input",
    "raw_output",
    "request_body",
    "response_body",
])
def test_packet_telemetry_rejects_raw_prompt_and_response_fields(field: str):
    telemetry = {**valid_packet_telemetry(), field: "raw data must not be logged"}

    with pytest.raises(ValidationError, match=field):
        validate("packet-telemetry.schema.json", telemetry)


@pytest.mark.parametrize("field", [
    "api_key",
    "token",
    "secret",
    "password",
    "base_url",
    "endpoint",
    "path",
])
def test_packet_telemetry_rejects_secret_or_private_metadata_keys(field: str):
    telemetry = {**valid_packet_telemetry(), field: "must not be present"}

    with pytest.raises(ValidationError, match=field):
        validate("packet-telemetry.schema.json", telemetry)


def test_packet_telemetry_accepts_failure_without_raw_traceback():
    telemetry = {
        **valid_packet_telemetry(),
        "status": "failure",
        "status_fields": {
            **valid_packet_telemetry()["status_fields"],
            "local_lane_status": "failure",
        },
        "error": {
            "error_class": "TimeoutError",
            "error_message_digest": "sha256:" + "a" * 64,
        },
    }

    validate("packet-telemetry.schema.json", telemetry)


def test_packet_telemetry_python_api_round_trips_schema_valid_dict():
    from sovereignty import PacketTelemetry

    telemetry = PacketTelemetry.from_dict(valid_packet_telemetry())

    assert telemetry.to_dict() == valid_packet_telemetry()
    validate("packet-telemetry.schema.json", telemetry.to_dict())


def test_packet_telemetry_rejects_raw_field_names_recursively():
    from sovereignty import PacketTelemetry, SovereigntyPolicyError

    telemetry = valid_packet_telemetry()
    telemetry["cost_accounting"] = {"base_url": "http://127.0.0.1:11434/v1"}

    with pytest.raises(SovereigntyPolicyError, match="base_url"):
        PacketTelemetry.from_dict(telemetry)


def test_build_error_digest_returns_sha256_digest_without_raw_message():
    from sovereignty import build_error_digest

    raw_message = "Traceback with private path /Users/monty/secret.py and token abc"
    digest = build_error_digest(raw_message)

    assert re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
    assert raw_message not in digest
    assert "/Users/monty" not in digest
