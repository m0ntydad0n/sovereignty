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
