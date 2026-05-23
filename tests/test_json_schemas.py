from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load_schema(name: str) -> dict:
    path = SCHEMAS / name
    with path.open() as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return schema


def validate(name: str, instance: dict) -> None:
    Draft202012Validator(load_schema(name)).validate(instance)


VALID_EXPOSURE = {
    "classification": "summary",
    "trust_model": "caller_attested",
    "evidence": None,
}

VALID_SIDE_EFFECT = {
    "effect_id": "fx_1",
    "effect_type": "send_message",
    "tool": "slack",
    "intent": "send the reviewed draft",
    "target": {"kind": "channel", "label": "engineering"},
    "payload": {"text": "Approved draft."},
    "risk": "medium",
}

VALID_REVIEW_PACKET = {
    "schema_version": "0.1",
    "packet_id": "pkt_1",
    "lane": "writer",
    "action": "draft",
    "local_output": {"draft": "Approved draft."},
    "model_metadata": {"provider": "ollama", "model": "qwen3:8b"},
    "exposure": VALID_EXPOSURE,
    "side_effects": [VALID_SIDE_EFFECT],
    "review_required": True,
}

VALID_MEASURED_REPORT = {
    "schema_version": "0.1",
    "trust_model": "measured",
    "classification": "excerpt",
    "verifier_id": "sovereignty.recording_proxy.v0",
    "observed_request_count": 1,
    "transmitted_byte_count": 123,
    "evidence": {
        "local_input_digest": "sha256:" + "a" * 64,
        "request_digests": ["sha256:" + "b" * 64],
        "observed_methods": ["POST"],
        "observed_url_schemes": ["https"],
    },
    "limitations": ["measurement only covers configured boundary"],
}


def test_all_public_schema_files_exist_and_are_valid_json_schema():
    for name in [
        "exposure.schema.json",
        "side-effect-proposal.schema.json",
        "review-packet.schema.json",
        "measured-exposure-report.schema.json",
        "packet-telemetry.schema.json",
        "side-effect-review-record.schema.json",
        "policy.schema.json",
        "guardrail-event.schema.json",
        "lane-health.schema.json",
    ]:
        load_schema(name)


def test_valid_protocol_fixtures_match_schemas():
    validate("exposure.schema.json", VALID_EXPOSURE)
    validate("side-effect-proposal.schema.json", VALID_SIDE_EFFECT)
    validate("review-packet.schema.json", VALID_REVIEW_PACKET)
    validate("measured-exposure-report.schema.json", VALID_MEASURED_REPORT)


def test_review_packet_schema_rejects_missing_required_fields():
    packet = dict(VALID_REVIEW_PACKET)
    del packet["packet_id"]

    with pytest.raises(ValidationError, match="packet_id"):
        validate("review-packet.schema.json", packet)


def test_side_effect_schema_rejects_execution_state():
    proposal = {**VALID_SIDE_EFFECT, "executed_at": "2026-05-22T00:00:00Z"}

    with pytest.raises(ValidationError, match="executed_at"):
        validate("side-effect-proposal.schema.json", proposal)


def test_side_effect_schema_rejects_unknown_risk():
    proposal = {**VALID_SIDE_EFFECT, "risk": "catastrophic"}

    with pytest.raises(ValidationError, match="catastrophic"):
        validate("side-effect-proposal.schema.json", proposal)


def test_review_packet_schema_rejects_secret_model_metadata_keys():
    packet = {
        **VALID_REVIEW_PACKET,
        "model_metadata": {
            "provider": "local",
            "api_key": "sk-not-real",
        },
    }

    with pytest.raises(ValidationError, match="api_key"):
        validate("review-packet.schema.json", packet)
