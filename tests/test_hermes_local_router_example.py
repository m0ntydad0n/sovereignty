import json
import os
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from sovereignty import validate_packet_dict


def _load_schema(name: str) -> dict:
    with (ROOT / "schemas" / name).open() as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return schema


def _validate_schema(name: str, instance: dict) -> None:
    Draft202012Validator(_load_schema(name)).validate(instance)


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


def test_real_hermes_local_router_example_emits_valid_packet_telemetry():
    payload = _run_example()
    telemetry = payload["packet_telemetry"]

    _validate_schema("packet-telemetry.schema.json", telemetry)
    assert telemetry["packet_id"] == payload["review_packet"]["packet_id"]
    assert telemetry["adapter"] == "hermes-local-router"
    assert telemetry["lane"] == "hermes.local_router.coder"
    assert telemetry["privacy"] == {
        "metadata_only": True,
        "raw_payload_logged": False,
        "local_output_logged": False,
    }


def test_real_hermes_local_router_example_emits_valid_broker_decision():
    payload = _run_example()
    decision = payload["broker_decision"]

    _validate_schema("broker-decision.schema.json", decision)
    assert decision["packet_id"] == payload["review_packet"]["packet_id"]
    assert decision["executed"] is False
    assert decision["budget"]["p95_ms"] == 8000
    assert decision["selected_backend_id"] == "direct:example:small-json"

    rejected = next(
        candidate
        for candidate in decision["candidates"]
        if candidate["backend_id"] == "openrouter:example/cheap-json"
    )
    assert rejected["eligible"] is False
    assert "privacy_gate_failed" in rejected["reason_codes"]
    assert "price_scored" not in rejected["stage"]


def test_real_hermes_local_router_example_telemetry_contains_no_raw_input_or_local_output():
    payload = _run_example()
    rendered = json.dumps(payload["packet_telemetry"], sort_keys=True)

    assert "LOCAL RAW INCIDENT" not in rendered
    assert "retry loop after failed issue sync" not in rendered
    assert "raw request bodies" not in rendered
    assert "api.example.invalid" not in rendered
    assert "/Users/" not in rendered
    assert "localhost" not in rendered
    assert "127.0.0.1" not in rendered
    assert "base_url" not in rendered


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
