import json

from sovereignty import (
    Exposure,
    ReviewPacket,
    SovereigntyPolicyError,
    validate_packet_dict,
)


def test_review_packet_round_trips_through_dict_and_json():
    packet = ReviewPacket(
        packet_id="pkt_roundtrip",
        lane="extractor",
        action="extract",
        local_output={"facts": ["deploy delayed"]},
        model_metadata={
            "provider": "ollama",
            "model": "qwen3:8b",
            "base_url": "http://localhost:11434/v1",
        },
        exposure=Exposure(classification="summary", trust_model="caller_attested"),
    )

    as_dict = packet.to_dict()
    assert as_dict["model_metadata"] == {"provider": "ollama", "model": "qwen3:8b"}

    parsed = ReviewPacket.from_dict(json.loads(packet.to_json()))

    assert parsed.to_dict() == as_dict


def test_validate_packet_dict_rejects_side_effect_without_review():
    data = {
        "schema_version": "0.1",
        "packet_id": "pkt_bad",
        "lane": "writer",
        "action": "draft",
        "local_output": {"draft": "send this"},
        "model_metadata": {"model": "local"},
        "exposure": {"classification": "summary", "trust_model": "caller_attested"},
        "side_effects": [{"type": "send_message"}],
        "review_required": False,
    }

    try:
        validate_packet_dict(data)
    except SovereigntyPolicyError as exc:
        assert "review_required" in str(exc)
    else:
        raise AssertionError("side-effect packet without review must fail")


def test_validate_packet_dict_requires_measured_exposure_evidence():
    data = {
        "schema_version": "0.1",
        "packet_id": "pkt_measured",
        "lane": "extractor",
        "action": "classify",
        "local_output": {"classification": "private"},
        "model_metadata": {"model": "local"},
        "exposure": {"classification": "none", "trust_model": "measured"},
        "side_effects": [],
        "review_required": False,
    }

    try:
        validate_packet_dict(data)
    except SovereigntyPolicyError as exc:
        assert "evidence" in str(exc)
    else:
        raise AssertionError("measured exposure without evidence must fail")
