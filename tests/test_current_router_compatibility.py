import json
import os
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "hermes" / "local_router_review_packet.py"
HERMES_README = ROOT / "examples" / "hermes" / "README.md"
CURRENT_ROUTER_DOC = ROOT / "docs" / "current-router-compatibility.md"


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


def _load_schema(name: str) -> dict:
    with (ROOT / "schemas" / name).open() as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return schema


def test_example_maps_current_live_router_tool_metadata_to_sovereignty_packet():
    payload = _run_example()
    compat = payload["current_router_compatibility"]
    packet = payload["review_packet"]

    assert compat["registered_tool"] == "local_llm_router"
    assert compat["worker_profile"] == "local-coder"
    assert compat["model_used"] == {
        "profile": "local-coder",
        "provider": "custom:local",
        "model": "qwen3-coder-local",
        "context_length": 32768,
    }
    assert compat["lane_model_map"] == {
        "route": "local-extractor / llama3.2:3b",
        "classify": "local-extractor / llama3.2:3b",
        "extract": "local-extractor / llama3.2:3b",
        "thread-packet": "local-extractor / llama3.2:3b",
        "draft": "local-writer / qwen3-coder-local",
        "code_plan": "local-coder / qwen3-coder-local",
        "code_review": "local-coder / qwen3-coder-local",
        "traceback": "local-coder / qwen3-coder-local",
    }
    assert compat["raw_context_seen_by_cloud"] is False
    assert compat["actual_avoided_cloud_tokens"] > 0
    assert compat["potential_avoided_cloud_tokens"] >= compat["actual_avoided_cloud_tokens"]
    assert packet["model_metadata"]["worker_profile"] == compat["worker_profile"]
    assert packet["model_metadata"]["model_used"] == compat["model_used"]
    assert packet["model_metadata"]["lane_model_map"] == compat["lane_model_map"]


def test_example_telemetry_uses_current_router_token_accounting_without_leaking_live_infra():
    payload = _run_example()
    telemetry = payload["packet_telemetry"]
    compat = payload["current_router_compatibility"]

    Draft202012Validator(_load_schema("packet-telemetry.schema.json")).validate(telemetry)
    assert telemetry["token_accounting"]["raw_input_tokens_estimated"] == compat["raw_input_tokens_estimated"]
    assert telemetry["token_accounting"]["local_output_tokens_estimated"] == compat["local_output_tokens_estimated"]
    assert telemetry["token_accounting"]["exposed_to_cloud_tokens_estimated"] == compat["exposed_to_cloud_tokens_estimated"]
    assert telemetry["token_accounting"]["kept_local_tokens_estimated"] == compat["actual_avoided_cloud_tokens"]

    rendered = json.dumps(payload, sort_keys=True)
    for forbidden in [
        "http://localhost",
        "127.0.0.1",
        "28080",
        "11434",
        "/Users/",
        "base_url",
        "api_key",
        "secret",
        "bearer ",
    ]:
        assert forbidden.lower() not in rendered.lower()


def test_docs_define_current_router_boundary_and_metric_semantics():
    text = CURRENT_ROUTER_DOC.read_text() + "\n" + HERMES_README.read_text()

    for phrase in [
        "route / classify / extract",
        "local-extractor / llama3.2:3b",
        "draft",
        "local-writer / qwen3-coder-local",
        "code_plan / code_review / traceback",
        "local-coder / qwen3-coder-local",
        "thread-packet",
        "raw_context_seen_by_cloud=false",
        "actual_avoided_cloud_tokens",
        "potential savings",
        "router-era saved",
        "24h saved",
        "7d saved",
        "local_worker_tokens",
        "router_era_frontier_tokens",
    ]:
        assert phrase in text

    forbidden_claims = [
        "frontier avoided is billing truth",
        "local lanes may execute side effects",
        "raw prompts are logged",
    ]
    lowered = text.lower()
    for phrase in forbidden_claims:
        assert phrase not in lowered
