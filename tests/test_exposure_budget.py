from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from sovereignty import Exposure, PacketTelemetry, ReviewPacket, SovereigntyPolicyError

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load_schema(name: str) -> dict:
    with (SCHEMAS / name).open() as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return schema


def validate(name: str, instance: dict) -> None:
    Draft202012Validator(load_schema(name)).validate(instance)


def valid_budget_dict() -> dict:
    return {
        "schema_version": "0.1",
        "budget_id": "privacy-default",
        "max_cloud_exposure_classification": "summary",
        "max_exposed_tokens_estimated": 500,
        "max_raw_cloud_tokens_per_run": 0,
        "max_unmeasured_packets_per_day": 0,
        "max_side_effect_proposals_per_packet": 1,
        "max_local_latency_ms": 10000,
        "require_measured_for_privacy_claims": True,
    }


def valid_packet() -> ReviewPacket:
    return ReviewPacket(
        packet_id="pkt_1",
        lane="extractor",
        action="summarize",
        local_output={"summary": "metadata-only summary"},
        model_metadata={"provider": "local", "model": "local-small"},
        exposure=Exposure(
            classification="summary",
            trust_model="measured",
            evidence={"verifier_id": "sovereignty.recording_proxy.v0"},
        ),
        side_effects=[],
        review_required=False,
    )


def valid_telemetry() -> PacketTelemetry:
    return PacketTelemetry(
        run_id="run_1",
        packet_id="pkt_1",
        trace_id="trace_1",
        adapter="hermes-local-router",
        lane="extractor",
        action="summarize",
        status="success",
        status_fields={
            "local_lane_status": "success",
            "guardrail_status": "not_run",
            "exposure_status": "measured",
            "side_effect_status": "proposed_none",
        },
        timing={
            "started_at": "2026-05-23T12:00:00Z",
            "ended_at": "2026-05-23T12:00:01Z",
            "duration_ms": 1000,
        },
        token_accounting={
            "raw_input_tokens_estimated": 1000,
            "local_output_tokens_estimated": 100,
            "exposed_to_cloud_tokens_estimated": 100,
            "kept_local_tokens_estimated": 900,
        },
    )


def test_exposure_budget_schema_accepts_valid_budget():
    validate("exposure-budget.schema.json", valid_budget_dict())


def test_exposure_budget_schema_rejects_unknown_max_classification():
    budget = {**valid_budget_dict(), "max_cloud_exposure_classification": "unknown"}

    with pytest.raises(ValidationError, match="unknown"):
        validate("exposure-budget.schema.json", budget)


def test_valid_summary_packet_under_budget_passes():
    from sovereignty import ExposureBudget

    budget = ExposureBudget.from_dict(valid_budget_dict())

    assert budget.validate_packet(valid_packet()).packet_id == "pkt_1"


def test_raw_exposure_fails_when_max_is_summary():
    from sovereignty import ExposureBudget

    budget = ExposureBudget.from_dict(valid_budget_dict())
    packet = valid_packet()
    packet.exposure = Exposure(classification="raw", trust_model="measured", evidence={"verifier_id": "ok"})

    with pytest.raises(SovereigntyPolicyError, match="raw"):
        budget.validate_packet(packet)


def test_unknown_exposure_fails_by_default():
    from sovereignty import ExposureBudget

    budget = ExposureBudget.from_dict(valid_budget_dict())
    packet = valid_packet()
    packet.exposure = Exposure(classification="unknown", trust_model="caller_attested", evidence=None)

    with pytest.raises(SovereigntyPolicyError, match="unknown"):
        budget.validate_packet(packet)


def test_too_many_side_effect_proposals_fails():
    from sovereignty import ExposureBudget

    budget = ExposureBudget.from_dict(valid_budget_dict())
    packet = valid_packet()
    packet.side_effects = [
        {
            "effect_id": "fx_1",
            "effect_type": "send_message",
            "tool": "slack",
            "intent": "send summary",
            "target": {},
            "payload": {},
            "risk": "medium",
        },
        {
            "effect_id": "fx_2",
            "effect_type": "create_issue",
            "tool": "github",
            "intent": "create issue",
            "target": {},
            "payload": {},
            "risk": "medium",
        },
    ]
    packet.review_required = True

    with pytest.raises(SovereigntyPolicyError, match="side-effect proposals"):
        budget.validate_packet(packet)


def test_exposed_token_count_over_max_fails():
    from sovereignty import ExposureBudget

    budget = ExposureBudget.from_dict(valid_budget_dict())
    telemetry = valid_telemetry()
    telemetry.token_accounting["exposed_to_cloud_tokens_estimated"] = 501

    with pytest.raises(SovereigntyPolicyError, match="exposed tokens"):
        budget.validate_telemetry(telemetry)


def test_measured_required_but_caller_attested_fails():
    from sovereignty import ExposureBudget

    budget = ExposureBudget.from_dict(valid_budget_dict())
    packet = valid_packet()
    packet.exposure = Exposure(classification="summary", trust_model="caller_attested", evidence=None)

    with pytest.raises(SovereigntyPolicyError, match="measured"):
        budget.validate_packet(packet)
