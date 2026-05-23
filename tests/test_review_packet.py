from sovereignty import (
    Exposure,
    ReviewPacket,
    SovereigntyPolicyError,
    validate_packet,
)


def test_review_packet_requires_review_when_side_effects_are_proposed():
    packet = ReviewPacket(
        packet_id="pkt_1",
        lane="writer",
        action="draft",
        local_output={"draft": "Send this."},
        model_metadata={"model": "qwen-local"},
        exposure=Exposure(classification="summary", trust_model="caller_attested"),
        side_effects=[{"type": "send_message", "target": "slack"}],
        review_required=False,
    )

    try:
        validate_packet(packet)
    except SovereigntyPolicyError as exc:
        assert "review_required" in str(exc)
    else:
        raise AssertionError("packet with side effects must require review")


def test_review_packet_accepts_local_prep_without_side_effects():
    packet = ReviewPacket(
        packet_id="pkt_2",
        lane="extractor",
        action="extract",
        local_output={"facts": ["one"]},
        model_metadata={"provider": "ollama", "model": "qwen3:8b"},
        exposure=Exposure(classification="summary", trust_model="caller_attested"),
        side_effects=[],
        review_required=False,
    )

    assert validate_packet(packet) is packet
