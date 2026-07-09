import json
import os
import subprocess
import sys


CLI_ENV = {**os.environ, "PYTHONPATH": "src"}


def test_cli_validate_accepts_valid_packet(tmp_path):
    packet = {
        "schema_version": "0.1",
        "packet_id": "pkt_cli_valid",
        "lane": "extractor",
        "action": "extract",
        "local_output": {"facts": ["one"]},
        "model_metadata": {"model": "qwen3:8b", "base_url": "http://localhost:11434/v1"},
        "exposure": {"classification": "summary", "trust_model": "caller_attested"},
        "side_effects": [],
        "review_required": False,
    }
    path = tmp_path / "packet.json"
    path.write_text(json.dumps(packet))

    result = subprocess.run(
        [sys.executable, "-m", "sovereignty", "validate", str(path)],
        text=True,
        capture_output=True,
        check=False,
        env=CLI_ENV,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout)["ok"] is True


def test_cli_validate_rejects_invalid_packet(tmp_path):
    packet = {
        "schema_version": "0.1",
        "packet_id": "pkt_cli_invalid",
        "lane": "writer",
        "action": "draft",
        "local_output": {"draft": "send this"},
        "model_metadata": {"model": "local"},
        "exposure": {"classification": "summary", "trust_model": "caller_attested"},
        "side_effects": [{"type": "send_message"}],
        "review_required": False,
    }
    path = tmp_path / "packet.json"
    path.write_text(json.dumps(packet))

    result = subprocess.run(
        [sys.executable, "-m", "sovereignty", "validate", str(path)],
        text=True,
        capture_output=True,
        check=False,
        env=CLI_ENV,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "review_required" in payload["error"]


def test_cli_validate_accepts_broker_decision_packet(tmp_path):
    decision = {
        "schema_version": "0.1",
        "decision_id": "bd_cli_valid",
        "packet_id": "pkt_cli_valid",
        "lane": "code_review",
        "authority_level": "A0",
        "exposure_origin": "precloud_compacted",
        "exposure_state": "compact_cloud",
        "validator_required": True,
        "validator_pass": True,
        "execution_mode": "sync",
        "executed": False,
        "budget": {"mode": "sync", "p95_ms": 8000, "max_cost_usd": 0.01},
        "selected_backend_id": "direct:example:small-json",
        "eligible_backend_ids": ["direct:example:small-json"],
        "candidates": [
            {
                "backend_id": "direct:example:small-json",
                "provider": "example",
                "transport": "direct_provider",
                "model": "small-json",
                "privacy_class": "redacted_or_compact_cloud",
                "authority_class": "proposal_only",
                "p95_ms": 1200,
                "estimated_cost_usd": 0.002,
                "eligible": True,
                "stage": ["validator_gate", "privacy_gate", "authority_gate", "health_gate", "p95_gate", "price_scored"],
                "reason_codes": [],
            }
        ],
        "reason_code": "selected_cheapest_eligible_after_gates",
        "privacy": {"metadata_only": True, "raw_payload_logged": False, "local_output_logged": False},
    }
    path = tmp_path / "broker-decision.json"
    path.write_text(json.dumps(decision))

    result = subprocess.run(
        [sys.executable, "-m", "sovereignty", "validate", "--schema", "broker-decision", str(path)],
        text=True,
        capture_output=True,
        check=False,
        env=CLI_ENV,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["schema"] == "broker-decision"
    assert payload["decision"]["selected_backend_id"] == "direct:example:small-json"


def test_cli_validate_rejects_broker_decision_with_raw_payload(tmp_path):
    decision = {
        "schema_version": "0.1",
        "decision_id": "bd_cli_invalid",
        "packet_id": "pkt_cli_valid",
        "lane": "code_review",
        "authority_level": "A0",
        "exposure_origin": "precloud_compacted",
        "exposure_state": "compact_cloud",
        "validator_required": True,
        "validator_pass": True,
        "execution_mode": "none",
        "executed": False,
        "budget": {"mode": "shadow_only", "max_cost_usd": 0},
        "selected_backend_id": None,
        "eligible_backend_ids": [],
        "candidates": [],
        "reason_code": "privacy_gate_failed",
        "privacy": {"metadata_only": True, "raw_payload_logged": False, "local_output_logged": False},
        "request_body": {"text": "raw prompt must not be here"},
    }
    path = tmp_path / "broker-decision.json"
    path.write_text(json.dumps(decision))

    result = subprocess.run(
        [sys.executable, "-m", "sovereignty", "validate", "--schema", "broker-decision", str(path)],
        text=True,
        capture_output=True,
        check=False,
        env=CLI_ENV,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "request_body" in payload["error"]


def test_cli_redact_outputs_redacted_metadata(tmp_path):
    metadata = {
        "provider": "ollama",
        "model": "qwen3:8b",
        "api_key": "sk-not-real",
        "base_url": "http://localhost:11434/v1",
    }
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps(metadata))

    result = subprocess.run(
        [sys.executable, "-m", "sovereignty", "redact", str(path)],
        text=True,
        capture_output=True,
        check=False,
        env=CLI_ENV,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == {"provider": "ollama", "model": "qwen3:8b"}
