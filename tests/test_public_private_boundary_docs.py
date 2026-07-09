from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "public-private-boundary.md"
README = ROOT / "README.md"


def test_public_private_boundary_doc_names_what_public_and_private_mean():
    text = DOC.read_text()

    for phrase in [
        "Public Sovereignty",
        "Private router-core",
        "protocol contracts",
        "implementation details",
        "local-prep / cloud-authority",
        "stable contracts, not private wiring",
        "execution broker decision packet",
        "metadata-only",
    ]:
        assert phrase in text


def test_public_private_boundary_doc_forbids_operational_leakage():
    text = DOC.read_text()

    for phrase in [
        "local endpoints",
        "host paths",
        "raw prompts",
        "private telemetry",
        "API keys",
        "tokens",
        "provider base URLs",
        "live operational lane maps",
    ]:
        assert phrase in text

    forbidden_overclaims = [
        "guarantees privacy",
        "trustless",
        "publish the private router",
        "drop-in replacement for gateways",
    ]
    lowered = text.lower()
    for phrase in forbidden_overclaims:
        assert phrase not in lowered


def test_readme_links_public_private_boundary_doc():
    text = README.read_text()

    assert "docs/public-private-boundary.md" in text
    assert "public/private boundary" in text.lower()
