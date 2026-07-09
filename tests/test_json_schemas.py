from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
EXAMPLES = ROOT / "examples" / "contracts"


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

VALID_BROKER_DECISION = {
    "schema_version": "0.1",
    "decision_id": "bd_1",
    "packet_id": "pkt_1",
    "lane": "code_review",
    "authority_level": "A0",
    "exposure_origin": "precloud_compacted",
    "exposure_state": "compact_cloud",
    "validator_required": True,
    "validator_pass": True,
    "execution_mode": "sync",
    "executed": False,
    "budget": {
        "p95_ms": 8000,
        "max_cost_usd": 0.01,
        "mode": "sync",
    },
    "selected_backend_id": "direct:example:small-json",
    "eligible_backend_ids": ["direct:example:small-json"],
    "candidates": [
        {
            "backend_id": "direct:example:small-json",
            "provider": "example",
            "transport": "direct_provider",
            "model": "small-json",
            "privacy_class": "redacted_or_compact_cloud",
            "authority_class": "proposal_only",
            "p95_ms": 1200,
            "estimated_cost_usd": 0.002,
            "eligible": True,
            "stage": [
                "validator_gate",
                "privacy_gate",
                "authority_gate",
                "health_gate",
                "p95_gate",
                "price_scored",
            ],
            "reason_codes": [],
        },
        {
            "backend_id": "openrouter:example/cheap-json",
            "provider": "openrouter",
            "transport": "openrouter",
            "model": "example/cheap-json",
            "privacy_class": "raw_cloud_allowed",
            "authority_class": "proposal_only",
            "p95_ms": 900,
            "estimated_cost_usd": 0.0005,
            "eligible": False,
            "stage": ["validator_gate", "privacy_gate"],
            "reason_codes": ["privacy_gate_failed"],
        },
    ],
    "reason_code": "selected_cheapest_eligible_after_gates",
    "privacy": {
        "metadata_only": True,
        "raw_payload_logged": False,
        "local_output_logged": False,
    },
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
        "exposure-budget.schema.json",
        "broker-decision.schema.json",
    ]:
        load_schema(name)


def test_valid_protocol_fixtures_match_schemas():
    validate("exposure.schema.json", VALID_EXPOSURE)
    validate("side-effect-proposal.schema.json", VALID_SIDE_EFFECT)
    validate("review-packet.schema.json", VALID_REVIEW_PACKET)
    validate("measured-exposure-report.schema.json", VALID_MEASURED_REPORT)
    validate("broker-decision.schema.json", VALID_BROKER_DECISION)


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


def test_broker_decision_schema_requires_metadata_only_unexecuted_decisions():
    decision = {**VALID_BROKER_DECISION, "executed": True}

    with pytest.raises(ValidationError, match="True"):
        validate("broker-decision.schema.json", decision)


def test_broker_decision_schema_rejects_raw_payload_and_endpoint_keys():
    decision = {**VALID_BROKER_DECISION, "request_body": {"text": "raw prompt"}}

    with pytest.raises(ValidationError, match="request_body"):
        validate("broker-decision.schema.json", decision)

    candidate = {**VALID_BROKER_DECISION["candidates"][0], "base_url": "http://127.0.0.1:11434"}
    decision = {**VALID_BROKER_DECISION, "candidates": [candidate]}

    with pytest.raises(ValidationError, match="base_url"):
        validate("broker-decision.schema.json", decision)


def test_broker_decision_schema_requires_p95_budget_for_sync_mode():
    budget = {"max_cost_usd": 0.01, "mode": "sync"}
    decision = {**VALID_BROKER_DECISION, "budget": budget}

    with pytest.raises(ValidationError, match="p95_ms"):
        validate("broker-decision.schema.json", decision)


def test_public_broker_decision_example_fixtures_validate_and_stay_metadata_only():
    fixture_names = [
        "broker-decision-privacy-reject.json",
        "broker-decision-trust-reject.json",
        "broker-decision-price-selected.json",
        "broker-decision-fallback-selected.json",
    ]

    for fixture_name in fixture_names:
        path = EXAMPLES / fixture_name
        data = json.loads(path.read_text())
        validate("broker-decision.schema.json", data)
        serialized = json.dumps(data, sort_keys=True)
        assert "raw prompt" not in serialized.lower()
        assert "/Users/" not in serialized
        assert "localhost" not in serialized
        assert "127.0.0.1" not in serialized
        assert "base_url" not in serialized
        assert data["executed"] is False
        assert data["privacy"] == {
            "metadata_only": True,
            "raw_payload_logged": False,
            "local_output_logged": False,
        }


def test_public_broker_decision_example_fixtures_cover_expected_paths():
    decisions = {
        path.name: json.loads(path.read_text())
        for path in EXAMPLES.glob("broker-decision-*.json")
    }

    assert decisions["broker-decision-privacy-reject.json"]["reason_code"] == "privacy_gate_failed"
    assert decisions["broker-decision-privacy-reject.json"]["selected_backend_id"] is None
    assert "price_scored" not in decisions["broker-decision-privacy-reject.json"]["candidates"][0]["stage"]

    assert decisions["broker-decision-trust-reject.json"]["reason_code"] == "authority_gate_failed"
    assert decisions["broker-decision-trust-reject.json"]["selected_backend_id"] is None

    assert decisions["broker-decision-price-selected.json"]["reason_code"] == "selected_cheapest_eligible_after_gates"
    assert decisions["broker-decision-price-selected.json"]["selected_backend_id"] in decisions[
        "broker-decision-price-selected.json"
    ]["eligible_backend_ids"]

    assert decisions["broker-decision-fallback-selected.json"]["reason_code"] == "selected_fallback_after_p95_gate"
    assert decisions["broker-decision-fallback-selected.json"]["selected_backend_id"] in decisions[
        "broker-decision-fallback-selected.json"
    ]["eligible_backend_ids"]
