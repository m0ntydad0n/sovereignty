"""Runnable Hermes local-router integration example.

This script models a realistic Sovereignty handoff without depending on a
private Hermes profile, a host-local endpoint, or user-specific config.

Flow:
1. A main Hermes agent has raw local context.
2. A local prep lane performs code triage and proposes an issue draft.
3. The local lane returns a Sovereignty ReviewPacket, not a side effect.
4. A RecordingBoundary models the later main-agent/cloud-reviewer request and
   attaches measured exposure evidence without raw request bodies or endpoints.

Run from the repository root:

    PYTHONPATH=src python examples/hermes/local_router_review_packet.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sovereignty import Exposure, PacketTelemetry, RecordingBoundary, ReviewPacket, validate_packet

LOCAL_CONTEXT = """
LOCAL RAW INCIDENT: traceback shows a write path retry loop after a failed
issue sync. The local lane may summarize the bug and propose an issue, but it
must not create the issue itself.

Trace excerpt, intentionally kept local in this example:
- sync_issue() attempted create_issue after a transient network failure.
- retry_issue_sync() retried with the same payload three times.
- mark_review_required() was skipped because the retry path reused a stale state object.
- proposed remediation is to stop automated issue creation until the main agent reviews source.
- this private raw diagnostic text should be summarized into a compact review packet, not sent whole.
""".strip()

CURRENT_ROUTER_MODEL_USED = {
    "profile": "local-coder",
    "provider": "custom:local",
    "model": "qwen3-coder-local",
    "context_length": 32768,
}

CURRENT_ROUTER_LANE_MODEL_MAP = {
    "route": "local-extractor / llama3.2:3b",
    "classify": "local-extractor / llama3.2:3b",
    "extract": "local-extractor / llama3.2:3b",
    "thread-packet": "local-extractor / llama3.2:3b",
    "draft": "local-writer / qwen3-coder-local",
    "code_plan": "local-coder / qwen3-coder-local",
    "code_review": "local-coder / qwen3-coder-local",
    "traceback": "local-coder / qwen3-coder-local",
}


def local_prep_lane(raw_context: str) -> dict[str, Any]:
    """Pretend this is Hermes's local-router tool running on a local model.

    In a real Hermes deployment this function maps to a safe local prep lane,
    such as `local_llm_router(action="traceback" | "code_plan")`. The lane can
    inspect raw local context, but its output is only a reviewable summary and a
    side-effect proposal for the main Hermes agent.
    """

    return {
        "summary": "A retry loop after failed issue sync should be triaged before enabling automated issue creation.",
        "findings": [
            {
                "kind": "bug_risk",
                "severity": "medium",
                "claim": "Issue sync retries can repeat the same failed action without a visible review gate.",
                "evidence": "local traceback triage; raw traceback intentionally withheld from this example output",
            }
        ],
        "recommended_next_step": "Have the main Hermes agent review and optionally create a GitHub issue.",
    }


def build_review_packet() -> tuple[dict[str, Any], dict[str, Any]]:
    started_at = datetime.now(timezone.utc)
    local_output = local_prep_lane(LOCAL_CONTEXT)
    side_effect_proposal = {
        "effect_id": "effect_create_issue_001",
        "effect_type": "create_issue",
        "tool": "github_issue_create",
        "intent": "Track the retry-loop triage item if the main Hermes agent approves it.",
        "target": {
            "repository": "example-owner/example-repo",
            "tracker": "github_issues",
        },
        "payload": {
            "title": "Review issue-sync retry loop before automation",
            "body": "Local prep found a medium-risk retry-loop pattern. Main agent should inspect source before filing or fixing.",
            "labels": ["triage", "local-prep"],
        },
        "risk": "medium",
    }

    packet = ReviewPacket(
        packet_id=f"pkt_{uuid4().hex}",
        lane="hermes.local_router.coder",
        action="code_triage",
        local_output=local_output,
        model_metadata={
            "router": "hermes.local_llm_router",
            "worker_profile": "local-coder",
            "model_used": CURRENT_ROUTER_MODEL_USED,
            "lane_model_map": CURRENT_ROUTER_LANE_MODEL_MAP,
            "routing_reason": "code traceback triage stays in a local prep lane",
        },
        exposure=Exposure(
            classification="summary",
            trust_model="measured",
            evidence="measured_exposure_report_attached",
        ),
        side_effects=[side_effect_proposal],
        review_required=True,
    )
    packet = validate_packet(packet)

    reviewer_body = json.dumps(
        {
            "instruction": "Review this Sovereignty packet; do not execute side effects.",
            "review_packet": packet.to_dict(),
        },
        sort_keys=True,
    ).encode("utf-8")

    def fake_cloud_reviewer_transport(method: str, url: str, body: bytes) -> dict[str, Any]:
        return {
            "status": 200,
            "reviewer_received_bytes": len(body),
            "note": "fake reviewer transport; no network request was made",
        }

    boundary = RecordingBoundary(
        local_input=LOCAL_CONTEXT,
        transport=fake_cloud_reviewer_transport,
        verifier_id="sovereignty.examples.hermes.local_router.v0",
    )
    transport_response = boundary.request(
        "POST",
        "https://reviewer.example.invalid/v1/review",
        reviewer_body,
    )
    measured_report = boundary.report(drop_observed_bodies=True)
    raw_input_tokens = len(LOCAL_CONTEXT.split())
    local_output_tokens = len(json.dumps(local_output).split())
    exposed_to_cloud_tokens = len(reviewer_body.decode("utf-8").split())
    actual_avoided_cloud_tokens = max(0, raw_input_tokens - local_output_tokens)
    current_router_compatibility = {
        "registered_tool": "local_llm_router",
        "worker_profile": "local-coder",
        "model_used": CURRENT_ROUTER_MODEL_USED,
        "lane_model_map": CURRENT_ROUTER_LANE_MODEL_MAP,
        "raw_context_seen_by_cloud": False,
        "raw_input_tokens_estimated": raw_input_tokens,
        "local_output_tokens_estimated": local_output_tokens,
        "exposed_to_cloud_tokens_estimated": exposed_to_cloud_tokens,
        "actual_avoided_cloud_tokens": actual_avoided_cloud_tokens,
        "potential_avoided_cloud_tokens": max(actual_avoided_cloud_tokens, raw_input_tokens),
        "metric_note": "actual avoided tokens require pre-cloud/local-ingress raw context withholding; normal cloud-planner tool calls are potential savings only",
    }
    ended_at = datetime.now(timezone.utc)
    duration_ms = max(0.0, (ended_at - started_at).total_seconds() * 1000)
    telemetry = PacketTelemetry(
        run_id=f"run_{uuid4().hex}",
        packet_id=packet.packet_id,
        trace_id=f"trace_{uuid4().hex}",
        adapter="hermes-local-router",
        lane="hermes.local_router.coder",
        action="code_triage",
        status="success",
        status_fields={
            "local_lane_status": "success",
            "guardrail_status": "not_run",
            "exposure_status": "measured",
            "side_effect_status": "proposed_pending_review",
        },
        timing={
            "started_at": started_at.isoformat().replace("+00:00", "Z"),
            "ended_at": ended_at.isoformat().replace("+00:00", "Z"),
            "duration_ms": duration_ms,
        },
        token_accounting={
            "raw_input_tokens_estimated": raw_input_tokens,
            "local_output_tokens_estimated": local_output_tokens,
            "exposed_to_cloud_tokens_estimated": exposed_to_cloud_tokens,
            "kept_local_tokens_estimated": actual_avoided_cloud_tokens,
        },
    )
    broker_decision = {
        "schema_version": "0.1",
        "decision_id": f"bd_{uuid4().hex}",
        "packet_id": packet.packet_id,
        "trace_id": telemetry.trace_id,
        "lane": "hermes.local_router.coder",
        "authority_level": "A0",
        "exposure_origin": "precloud_compacted",
        "exposure_state": "compact_cloud",
        "validator_required": True,
        "validator_pass": True,
        "execution_mode": "sync",
        "executed": False,
        "budget": {
            "mode": "sync",
            "p95_ms": 8000,
            "max_cost_usd": 0.01,
        },
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
                "healthy": True,
                "eligible": True,
                "stage": [
                    "validator_gate",
                    "privacy_gate",
                    "authority_gate",
                    "health_gate",
                    "p95_gate",
                    "price_scored",
                ],
                "reason_codes": [],
            },
            {
                "backend_id": "openrouter:example/cheap-json",
                "provider": "openrouter",
                "transport": "openrouter",
                "model": "example/cheap-json",
                "privacy_class": "raw_cloud_allowed",
                "authority_class": "proposal_only",
                "p95_ms": 900,
                "estimated_cost_usd": 0.0005,
                "healthy": True,
                "eligible": False,
                "stage": ["validator_gate", "privacy_gate"],
                "reason_codes": ["privacy_gate_failed"],
            },
        ],
        "reason_code": "selected_cheapest_eligible_after_gates",
        "privacy": {
            "metadata_only": True,
            "raw_payload_logged": False,
            "local_output_logged": False,
        },
    }

    return {
        "review_packet": packet.to_dict(),
        "packet_telemetry": telemetry.to_dict(),
        "broker_decision": broker_decision,
        "current_router_compatibility": current_router_compatibility,
        "transport_response": transport_response,
        "hermes_mapping": {
            "local prep lane": "Hermes local-router worker performs code triage only",
            "main Hermes agent": "reviews packet, validates policy, and decides whether to answer or act",
            "side-effect proposal": "GitHub issue draft is review-only until an authority-bearing tool acts",
            "RecordingBoundary": "models measured exposure at the cloud-review handoff boundary",
        },
    }, measured_report


def main() -> None:
    payload, measured_report = build_review_packet()
    payload["measured_exposure_report"] = measured_report
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
