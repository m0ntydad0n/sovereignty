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


def valid_guardrail_event() -> dict:
    return {
        "schema_version": "0.1",
        "event_id": "gr_1",
        "policy_id": "default-local-prep",
        "stage": "pre_authority",
        "status": "passed",
        "started_at": "2026-05-23T12:00:00Z",
        "ended_at": "2026-05-23T12:00:01Z",
        "duration_ms": 1000,
        "guardrail_name": "metadata-only-check",
        "masked_entity_counts": {"email": 2},
        "intervention_type": "none",
    }


def test_valid_guardrail_event_schema_passes():
    validate("guardrail-event.schema.json", valid_guardrail_event())


@pytest.mark.parametrize("field", ["prompt", "response", "request_body", "response_body", "blocked_text"])
def test_guardrail_event_schema_rejects_raw_payload_fields(field: str):
    event = {**valid_guardrail_event(), field: "raw text"}

    with pytest.raises(ValidationError, match=field):
        validate("guardrail-event.schema.json", event)


def test_guardrail_event_schema_rejects_invalid_enum():
    event = {**valid_guardrail_event(), "stage": "during_everything"}

    with pytest.raises(ValidationError, match="during_everything"):
        validate("guardrail-event.schema.json", event)


def test_guardrail_event_python_api_round_trips_schema_valid_dict():
    from sovereignty import GuardrailEvent

    event = GuardrailEvent.from_dict(valid_guardrail_event())

    assert event.to_dict() == valid_guardrail_event()
    validate("guardrail-event.schema.json", event.to_dict())
