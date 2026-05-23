from sovereignty import (
    Exposure,
    ReviewPacket,
    SideEffectProposal,
    SovereigntyPolicyError,
    validate_packet,
    validate_side_effect_proposal,
)


VALID_PROPOSAL = {
    "effect_id": "fx_1",
    "effect_type": "send_message",
    "tool": "slack",
    "intent": "send the reviewed draft to the requested channel",
    "target": {"kind": "channel", "label": "engineering"},
    "payload": {"text": "Draft ready for reviewer approval."},
    "risk": "medium",
}


def test_valid_side_effect_proposal_is_accepted():
    proposal = validate_side_effect_proposal(dict(VALID_PROPOSAL))

    assert isinstance(proposal, SideEffectProposal)
    assert proposal.effect_id == "fx_1"
    assert proposal.risk == "medium"
    assert proposal.to_dict() == VALID_PROPOSAL


def test_packet_accepts_valid_side_effect_only_when_review_required():
    packet = ReviewPacket(
        packet_id="pkt_side_effect",
        lane="writer",
        action="draft",
        local_output={"draft": "Draft ready for reviewer approval."},
        model_metadata={"model": "qwen-local"},
        exposure=Exposure(classification="summary", trust_model="caller_attested"),
        side_effects=[dict(VALID_PROPOSAL)],
        review_required=True,
    )

    validated = validate_packet(packet)

    assert validated.side_effects == [VALID_PROPOSAL]


def test_side_effect_proposal_requires_required_fields():
    proposal = dict(VALID_PROPOSAL)
    del proposal["intent"]

    try:
        validate_side_effect_proposal(proposal)
    except SovereigntyPolicyError as exc:
        assert "intent" in str(exc)
    else:
        raise AssertionError("side-effect proposal without intent must be rejected")


def test_side_effect_proposal_rejects_unknown_risk():
    proposal = {**VALID_PROPOSAL, "risk": "catastrophic"}

    try:
        validate_side_effect_proposal(proposal)
    except SovereigntyPolicyError as exc:
        assert "risk" in str(exc)
    else:
        raise AssertionError("side-effect proposal with unknown risk must be rejected")


def test_side_effect_proposal_rejects_execution_state():
    proposal = {**VALID_PROPOSAL, "executed_at": "2026-05-22T00:00:00Z"}

    try:
        validate_side_effect_proposal(proposal)
    except SovereigntyPolicyError as exc:
        assert "execution" in str(exc)
    else:
        raise AssertionError("side-effect proposal must not contain execution state")


def test_packet_rejects_non_object_side_effects():
    packet = ReviewPacket(
        packet_id="pkt_bad_side_effect",
        lane="writer",
        action="draft",
        local_output={"draft": "Draft ready."},
        model_metadata={"model": "qwen-local"},
        exposure=Exposure(classification="summary", trust_model="caller_attested"),
        side_effects=["send this"],
        review_required=True,
    )

    try:
        validate_packet(packet)
    except SovereigntyPolicyError as exc:
        assert "side_effects[0]" in str(exc)
    else:
        raise AssertionError("non-object side effects must be rejected")
