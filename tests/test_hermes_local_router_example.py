import json
import os
import subprocess
import sys
from pathlib import Path

from sovereignty import validate_packet_dict


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "hermes" / "local_router_review_packet.py"
README = ROOT / "README.md"
HERMES_README = ROOT / "examples" / "hermes" / "README.md"


def _run_example() -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    proc = subprocess.run(
        [sys.executable, str(EXAMPLE)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    return json.loads(proc.stdout)


def test_real_hermes_local_router_example_emits_valid_review_packet():
    payload = _run_example()
    packet = validate_packet_dict(payload["review_packet"])

    assert packet.lane == "hermes.local_router.coder"
    assert packet.action == "code_triage"
    assert packet.exposure.classification == "summary"
    assert packet.exposure.trust_model == "measured"
    assert packet.review_required is True
    assert packet.side_effects[0]["effect_type"] == "create_issue"


def test_real_hermes_local_router_example_includes_measured_report_without_raw_or_private_infra():
    payload = _run_example()
    rendered = json.dumps(payload, sort_keys=True)
    report = payload["measured_exposure_report"]

    assert report["trust_model"] == "measured"
    assert report["observed_request_count"] == 1
    assert "raw request bodies are not included" in report["limitations"]
    assert "LOCAL RAW INCIDENT" not in rendered
    assert "api.example.invalid" not in rendered
    assert "/Users/" not in rendered
    assert "localhost" not in rendered
    assert "127.0.0.1" not in rendered
    assert "sk-live" not in rendered.lower()
    assert "bearer " not in rendered.lower()


def test_real_hermes_local_router_example_documents_mapping_and_is_linked():
    assert EXAMPLE.exists()
    example_text = EXAMPLE.read_text()
    hermes_text = HERMES_README.read_text()
    readme_text = README.read_text()

    for phrase in [
        "local prep lane",
        "main Hermes agent",
        "ReviewPacket",
        "side-effect proposal",
        "RecordingBoundary",
    ]:
        assert phrase in example_text or phrase in hermes_text

    assert "examples/hermes/local_router_review_packet.py" in readme_text
    assert "local-router integration" in readme_text
