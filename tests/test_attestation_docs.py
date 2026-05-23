from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "attestation.md"


def test_attestation_doc_covers_digest_signing_boundary_and_threats():
    text = DOC.read_text()

    for phrase in [
        "JWS",
        "packet_digest",
        "policy_digest",
        "expires_at",
        "key_id",
        "jwks_url",
        "does not prove",
        "replay",
        "stolen signing key",
        "bypassing verifier",
        "forged local packet",
        "side-effect review records",
    ]:
        assert phrase in text

    assert "sign raw packet payloads" not in text.lower()
