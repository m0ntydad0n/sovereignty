from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "protocol-not-gateway.md"
README = ROOT / "README.md"
SPEC = ROOT / "SPEC.md"


def test_protocol_not_gateway_design_note_exists_with_sober_comparison_dimensions():
    assert DOC.exists()
    text = DOC.read_text()

    required_phrases = [
        "Sovereignty is a protocol, not a gateway",
        "Provider routing",
        "Cost and fallback policy",
        "Retries and rate limits",
        "Observability and billing",
        "Review packets",
        "Authority gating",
        "Exposure accounting",
        "caller_attested",
        "measured",
        "Side-effect proposals",
        "Composing with gateways",
        "LiteLLM",
        "RouteLLM",
        "Portkey",
    ]
    for phrase in required_phrases:
        assert phrase in text


def test_protocol_not_gateway_design_note_avoids_manifesto_and_overclaim_language():
    text = DOC.read_text().lower()

    forbidden_phrases = [
        "revolutionary",
        "paradigm shift",
        "trustless",
        "guarantees privacy",
        "solves privacy",
        "replacement for gateways",
        "kills",
        "destroys",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in text


def test_readme_links_protocol_not_gateway_design_note():
    text = README.read_text()

    assert "docs/protocol-not-gateway.md" in text
    assert "protocol, not a gateway" in text


def test_spec_points_to_positioning_note_from_non_goals_or_compatibility():
    text = SPEC.read_text()

    assert "docs/protocol-not-gateway.md" in text
    assert "compose with gateways" in text
