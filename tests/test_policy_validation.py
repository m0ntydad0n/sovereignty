from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from sovereignty import Exposure, ReviewPacket, SovereigntyPolicyError

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load_schema(name: str) -> dict:
    with (SCHEMAS / name).open() as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return schema


def validate(name: str, instance: dict) -> None:
    Draft202012Validator(load_schema(name)).validate(instance)


def valid_policy_dict() -> dict:
    return {
        "schema_version": "0.1",
        "policy_id": "default-local-prep",
        "trusted_verifier_ids": ["sovereignty.recording_proxy.v0"],
        "max_cloud_exposure_classification": "summary",
        "require_measured_exposure_for_privacy_claims": True,
        "trusted_metadata_origins": ["authority", "verifier"],
        "forbidden_client_metadata_keys": [
            "policy_tags",
            "budget_tags",
            "authority_tags",
            "trust_tags",
        ],
        "forbidden_side_effect_types": ["deploy", "trade", "payment"],
        "risk_floor_by_effect_type": {"send_message": "medium", "deploy": "high"},
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


def test_policy_schema_accepts_valid_policy():
    validate("policy.schema.json", valid_policy_dict())


def test_policy_schema_rejects_forbidden_client_metadata_shape_errors():
    policy = {**valid_policy_dict(), "trusted_metadata_origins": ["caller"]}

    with pytest.raises(ValidationError, match="caller"):
        validate("policy.schema.json", policy)


def test_trust_model_measured_with_untrusted_verifier_id_fails():
    from sovereignty import SovereigntyPolicy

    policy = SovereigntyPolicy.from_dict(valid_policy_dict())
    packet = valid_packet()
    packet.exposure = Exposure(
        classification="summary",
        trust_model="measured",
        evidence={"verifier_id": "untrusted.verifier"},
    )

    with pytest.raises(SovereigntyPolicyError, match="untrusted.verifier"):
        policy.validate_packet(packet, metadata_origin="local_lane")


def test_trust_model_measured_with_trusted_verifier_and_valid_evidence_passes():
    from sovereignty import SovereigntyPolicy

    policy = SovereigntyPolicy.from_dict(valid_policy_dict())
    packet = policy.validate_packet(valid_packet(), metadata_origin="local_lane")

    assert packet.packet_id == "pkt_1"


@pytest.mark.parametrize("key", ["policy_tags", "budget_tags", "authority_tags", "trust_tags"])
def test_local_or_client_metadata_containing_trusted_policy_tags_fails(key: str):
    from sovereignty import SovereigntyPolicy

    policy = SovereigntyPolicy.from_dict(valid_policy_dict())
    packet = valid_packet()
    packet.model_metadata[key] = ["gold"]

    with pytest.raises(SovereigntyPolicyError, match=key):
        policy.validate_packet(packet, metadata_origin="local_lane")


def test_authority_origin_can_attach_policy_tags():
    from sovereignty import SovereigntyPolicy

    policy = SovereigntyPolicy.from_dict(valid_policy_dict())
    packet = valid_packet()
    packet.model_metadata["policy_tags"] = ["authority-reviewed"]

    validated = policy.validate_packet(packet, metadata_origin="authority")

    assert validated.model_metadata["policy_tags"] == ["authority-reviewed"]


def test_risk_downgrade_below_floor_fails():
    from sovereignty import SovereigntyPolicy

    policy = SovereigntyPolicy.from_dict(valid_policy_dict())
    packet = valid_packet()
    packet.side_effects = [
        {
            "effect_id": "fx_1",
            "effect_type": "send_message",
            "tool": "slack",
            "intent": "send reviewed summary",
            "target": {"kind": "channel"},
            "payload": {"text": "Summary"},
            "risk": "low",
        }
    ]
    packet.review_required = True

    with pytest.raises(SovereigntyPolicyError, match="risk floor"):
        policy.validate_packet(packet, metadata_origin="local_lane")


def test_forbidden_side_effect_type_fails():
    from sovereignty import SovereigntyPolicy

    policy = SovereigntyPolicy.from_dict(valid_policy_dict())
    packet = valid_packet()
    packet.side_effects = [
        {
            "effect_id": "fx_1",
            "effect_type": "payment",
            "tool": "payments",
            "intent": "pay invoice",
            "target": {"vendor": "example"},
            "payload": {"amount": "10.00"},
            "risk": "high",
        }
    ]
    packet.review_required = True

    with pytest.raises(SovereigntyPolicyError, match="payment"):
        policy.validate_packet(packet, metadata_origin="local_lane")


def test_policy_allows_summary_exposure_and_no_side_effects():
    from sovereignty import SovereigntyPolicy

    policy = SovereigntyPolicy.from_dict(valid_policy_dict())

    assert policy.validate_packet(valid_packet(), metadata_origin="local_lane").packet_id == "pkt_1"
