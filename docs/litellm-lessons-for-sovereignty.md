# LiteLLM lessons for Sovereignty

Date: 2026-05-23

Purpose: Pull useful product and protocol patterns from LiteLLM's public docs without copying LiteLLM's gateway layer. Sovereignty should remain a local-prep / cloud-authority protocol, but LiteLLM is a strong reference for operational maturity around routing, identity, budgets, guardrails, observability, and reliability.

## Source set reviewed

Primary local docs clone: `/tmp/litellm_docs_repo` from `https://github.com/BerriAI/litellm-docs`.

Key docs inspected:

- `docs/routing.md`
- `docs/proxy/configs.md`
- `docs/proxy/virtual_keys.md`
- `docs/proxy/team_budgets.md`
- `docs/proxy/provider_budget_routing.md`
- `docs/proxy/keys_teams_router_settings.md`
- `docs/proxy/health_check_routing.md`
- `docs/proxy/guardrails/custom_guardrail.md`
- `docs/proxy/guardrails/team_based_guardrails.md`
- `docs/proxy/guardrails/guardrail_policies.md`
- `docs/proxy/logging_spec.md`
- `docs/observability/scrub_data.md`
- `docs/proxy/reject_clientside_metadata_tags.md`
- `docs/proxy/caching.md`
- `docs/caching/all_caches.md`
- `docs/completion/prompt_compression.md`
- `docs/proxy/custom_pricing.md`
- `docs/proxy/dynamic_rate_limit.md`
- `docs/proxy/team_logging.md`
- `docs/proxy/alerting.md`
- `docs/mcp_zero_trust.md`
- `docs/mcp_semantic_filter.md`

Sovereignty files compared:

- `SPEC.md`
- `README.md`
- `THREAT_MODEL.md`
- `docs/protocol-not-gateway.md`
- `schemas/review-packet.schema.json`
- `schemas/measured-exposure-report.schema.json`
- `schemas/side-effect-proposal.schema.json`
- `src/sovereignty/packet.py`
- `src/sovereignty/measured_exposure.py`
- `src/sovereignty/redaction.py`

## Executive takeaways

LiteLLM is a gateway. Sovereignty should not become that. The useful extraction is not provider routing itself; it is the operational discipline around every call:

1. Identity-scoped policy: key/team/global overrides, with clear resolution order.
2. Budget and quota semantics: budget by provider/model/tag/team, plus reset windows.
3. Health and reliability records: deployment IDs, cooldowns, retries, failure classes, health checks.
4. Standard logging payloads: trace IDs, status fields, token/cost fields, guardrail results, cache hits.
5. Guardrail lifecycle: pre-call, in-stream/during-call, post-call; policies that group guardrails and attach to scopes.
6. Metadata integrity: tags that influence routing/budgets should be authority-issued, not client supplied.
7. Log scrubbing and alert redaction: logs and alerts are a privacy surface, not just observability.
8. Shadow experiments: traffic mirroring lets you evaluate a secondary model without affecting primary behavior.
9. Signed tool boundaries: MCP zero-trust JWT signing is highly relevant to proving that side-effect/tool calls passed through the authority boundary.
10. Local/on-prem pricing model: zero-cost local models need explicit cost semantics so budgets do not behave accidentally.

The strongest next step is to add a Sovereignty `RunRecord` / `PacketTelemetry` schema and a policy-resolution layer. That would move the project from packet validation into repeatable operations while preserving the protocol-not-gateway positioning.

## What LiteLLM does that is worth adapting

### 1. Hierarchical policy resolution

LiteLLM has key/team/global router settings: key-level settings win over team-level settings, and global settings are fallback. The docs call out per-key/per-team routing strategies, fallback chains, timeouts, retries, and reliability settings.

For Sovereignty, adapt the pattern but not the gateway behavior:

- Define policy scopes such as `global`, `workspace`, `profile`, `lane`, and `caller`.
- Resolve policy deterministically.
- Use most-restrictive semantics for safety-critical fields, especially side effects and exposure claims.
- Do not let the packet itself promote its authority level.

Candidate Sovereignty policy fields:

```json
{
  "schema_version": "0.1",
  "policy_id": "default-local-prep",
  "scope": {"profile": "ringer", "lane": "local-extractor"},
  "allowed_actions": ["classify", "extract", "summarize", "draft"],
  "forbidden_side_effect_types": ["send_message", "deploy", "trade", "payment"],
  "max_raw_cloud_exposure": "summary",
  "require_measured_exposure_for": ["privacy_claims", "public_reports"],
  "require_review_for_risk": ["low", "medium", "high"],
  "max_latency_ms": 30000,
  "max_exposed_tokens": 1000
}
```

This strengthens Sovereignty without becoming a LiteLLM clone.

### 2. Authority-issued metadata, not client-side steering

LiteLLM has a setting to reject client-side `metadata.tags` because tags can affect budget tracking and routing. Tags should be inherited from the API key metadata instead.

Sovereignty equivalent:

- Packets may include `request_metadata`, but fields that affect trust, billing, routing, or approval must come from the authority layer or verifier.
- A local lane cannot self-assert `trust_model: measured` unless the measured-exposure evidence validates against a known verifier.
- A local lane cannot mark a side effect approved, executed, or safe just by adding metadata.

Recommended schema hardening:

- Keep `exposure.trust_model` strict.
- Add `issuer` / `verifier_id` allowlist checks in policy validation.
- Add `metadata_origin` for sensitive labels: `caller`, `local_lane`, `authority`, `verifier`.
- Reject client-supplied `policy_tags`, `trust_tags`, or `budget_tags` unless the policy explicitly allows them.

### 3. Standard telemetry payload

LiteLLM's standard logging payload is broad: unique ID, trace ID, call type, response cost, cost breakdown, status/status fields, tokens, start/end timing, time-to-first-token, model/deployment metadata, cache hit, request tags, end user, error information, applied guardrails, and hidden params.

Sovereignty already has packet-level telemetry in Hermes. The next durable improvement is a language-agnostic metadata-only telemetry schema:

```json
{
  "schema_version": "0.1",
  "run_id": "run_...",
  "packet_id": "pkt_...",
  "trace_id": "trace_...",
  "parent_session_id": "...",
  "adapter": "hermes-local-router",
  "lane": "local-extractor",
  "action": "classify",
  "status": "success",
  "status_fields": {
    "local_lane_status": "success",
    "guardrail_status": "not_run",
    "exposure_status": "measured",
    "side_effect_status": "proposed_none"
  },
  "token_accounting": {
    "raw_input_tokens_estimated": 12345,
    "local_output_tokens_estimated": 432,
    "exposed_to_cloud_tokens_estimated": 432,
    "kept_local_tokens_estimated": 11913
  },
  "timing": {
    "started_at": "...",
    "ended_at": "...",
    "duration_ms": 1840
  },
  "cost_accounting": {
    "local_cost_usd": 0,
    "cloud_cost_usd_estimated": 0.0042,
    "avoided_cloud_cost_usd_estimated": 0.118
  },
  "privacy": {
    "raw_payload_logged": false,
    "local_output_logged": false,
    "metadata_only": true
  }
}
```

Important: do not log raw prompts or local outputs. LiteLLM logs can include `messages` and `response`; Sovereignty should explicitly diverge and make metadata-only logging the default protocol stance.

### 4. Guardrail lifecycle and policies

LiteLLM supports custom guardrails that can run pre-call, post-call, and over streaming output. It also has guardrail policies that group guardrails and attach them to scopes, plus team bring-your-own guardrails with admin review.

Sovereignty can use this as an authority-boundary concept:

- `pre_local_guardrails`: checks before local lane sees input, e.g. maximum size, allowed file type, no side-effect tool references.
- `post_local_guardrails`: checks local output before it becomes a review packet, e.g. no secret echoing, valid JSON, no forged approval fields.
- `pre_authority_guardrails`: checks before main agent acts on packet, e.g. side-effect risk escalation, human-review gates.
- `post_authority_guardrails`: checks final answer/action proposal before user-visible output or tool execution.

Recommended packet addition:

```json
"applied_policies": [
  {
    "policy_id": "no-secret-echo-v1",
    "stage": "post_local",
    "status": "passed",
    "intervention": "none",
    "duration_ms": 12
  }
]
```

This should be metadata-only. It should not include the text that triggered the guardrail.

### 5. Reliability and local-lane health

LiteLLM has mature reliability semantics: weighted deployments, priority ordering, weighted failover, deployment-level cooldowns, max parallel requests, retries, retry policies by exception type, and proactive health-check routing.

Sovereignty should not route all model traffic, but adapters should expose local-lane health and reliability as metadata:

- stable lane IDs;
- deterministic run IDs;
- local lane status: `healthy`, `degraded`, `cooldown`, `unavailable`;
- failure class: `timeout`, `invalid_json`, `policy_violation`, `process_error`, `guardrail_intervened`;
- cooldown hints;
- max concurrency hints;
- timeout and retry policy used.

This improves the Hermes router without turning Sovereignty into a gateway. The main agent can decide: retry local, switch local lane, request human review, or fall back to cloud.

### 6. Health checks before user-visible failure

LiteLLM's health-check routing proactively removes bad deployments from routing before a user hits them. It also allows failure policies by error type so transient failures do not eject a deployment too aggressively.

Sovereignty adaptation:

- Add adapter-level health check contract, not provider routing.
- Define a minimal `LaneHealth` schema:

```json
{
  "schema_version": "0.1",
  "lane": "local-extractor",
  "checked_at": "...",
  "status": "healthy",
  "latency_ms": 210,
  "last_success_at": "...",
  "last_failure_class": null,
  "cooldown_until": null
}
```

The Hermes local router can use this to avoid calling a cold or wedged writer lane synchronously.

### 7. Budgets should include exposure, not only dollars

LiteLLM budgets spend by key/user/team/provider/model/tag and can reset over windows. It also has provider/model/tag budget routing and dynamic TPM/RPM allocation.

Sovereignty's differentiated move: define privacy and authority budgets.

Possible budget dimensions:

- `max_raw_cloud_tokens_per_run`
- `max_exposed_summary_tokens_per_run`
- `max_side_effect_proposals_per_packet`
- `max_local_latency_ms`
- `max_cloud_cost_usd_per_review`
- `max_unmeasured_packets_per_day`
- `max_failed_guardrails_per_window`

This maps LiteLLM's operational budget discipline into Sovereignty's privacy/authority layer.

### 8. Cost accounting for local-first wins

LiteLLM has detailed custom pricing, including zero-cost on-prem models that bypass budget checks only when input and output costs are explicitly set to zero. It also supports cost breakdowns and model cost maps.

For Sovereignty:

- Add optional `pricing_basis` metadata for adapters.
- Track local cost as zero or configured amortized cost.
- Track cloud avoided-cost estimates separately from actual spend.
- Require `pricing_source` and `pricing_version` so reports are reproducible.
- Keep avoided-cost as estimated unless calculated from actual provider pricing at run time.

This directly supports the existing Hermes router-effectiveness report.

### 9. Shadow evaluation / traffic mirroring

LiteLLM traffic mirroring sends production traffic to a secondary silent model for evaluation without affecting latency or the primary response.

Sovereignty adaptation:

- Mirror local-prep tasks to candidate local lanes for evaluation.
- Never let the shadow lane propose or execute side effects.
- Log only metadata and scored outputs where allowed.
- Use this for quality benchmarks: local-extractor A vs B, writer lane latency, classifier false negatives.

This is a clean way to improve local lanes while keeping main-agent authority unchanged.

### 10. Prompt compression and retrieval handles

LiteLLM prompt compression can replace large content with stubs and keep a cache so a model can retrieve omitted content through a tool call.

For Sovereignty, this is dangerous but useful if constrained:

- A local lane may produce a compact summary and local-only retrieval handles.
- The cloud/main agent must not automatically retrieve raw handles unless policy allows raw exposure.
- Retrieval events should update exposure classification from `summary` to `excerpt` or `raw` depending on what is retrieved.

Recommended protocol idea:

```json
"local_references": [
  {
    "ref_id": "local_ref_1",
    "kind": "omitted_context",
    "digest": "sha256:...",
    "retrievable_by_cloud": false,
    "requires_authority": true
  }
]
```

This preserves the value of compression without silently leaking raw context later.

### 11. Signed authority/tool boundary

LiteLLM's MCP zero-trust docs are highly relevant: outbound MCP tool calls can be signed with short-lived RS256 JWTs; the MCP server verifies JWKS so direct calls that bypass the gateway are rejected.

Sovereignty analogue:

- Sign review packets or side-effect proposals at the local-prep boundary.
- Authority tools can verify that a proposed side effect passed through a known Sovereignty validator before execution.
- Include short TTL, issuer, audience, packet digest, policy digest, and review state digest.
- Do not put raw payloads in the signature claims; sign digests.

Possible future schema:

```json
"attestation": {
  "type": "jws",
  "issuer": "sovereignty-local-boundary",
  "audience": "hermes-authority-tools",
  "packet_digest": "sha256:...",
  "policy_digest": "sha256:...",
  "expires_at": "...",
  "jwks_url": "https://.../.well-known/jwks.json"
}
```

This is one of the biggest ideas to pull forward. It makes the side-effect boundary enforceable rather than merely documented.

### 12. Alerts and incident semantics

LiteLLM alerting covers hanging API calls, slow calls, failed calls, outages, budget alerts, spend reports, and DB failures. It explicitly supports redacting messages from alerts.

Sovereignty equivalent alerts:

- packet validation failures;
- measured exposure mismatch, e.g. local claimed `summary` but verifier saw `raw`;
- local lane repeated timeouts;
- side-effect proposal without `review_required`;
- policy tag supplied by local/client instead of authority;
- guardrail technical failure;
- unmeasured exposure used in a public/privacy claim;
- packet contains redacted metadata fields.

Alerts must be metadata-only by default.

## Recommended implementation backlog

### P0: Packet telemetry schema

Add `schemas/packet-telemetry.schema.json` and Python dataclass.

Why: Hermes already emits `router_packets.jsonl`; standardizing this turns the telemetry into part of the protocol ecosystem.

Fields:

- IDs: `run_id`, `packet_id`, `trace_id`, `consumer_session_id`, `adapter`.
- Status: `success`, `failure`, `timeout`, `policy_blocked`.
- Status fields: local lane, guardrail, exposure, side effect.
- Timing: start/end/duration.
- Token accounting: raw/local/exposed/kept-local.
- Cost accounting: actual/estimated/avoided.
- Privacy flags: no raw prompt/output logged.
- Error class only, not traceback text unless redacted.

Tests:

- rejects raw `messages` or `response` fields;
- rejects private paths/base URLs/API keys;
- requires packet/session linkage when adapter is Hermes;
- validates failure packets.

### P0: Side-effect lifecycle outside proposal schema

Current side-effect proposal schema correctly excludes execution/approval state. Keep that. Add a separate authority-side record:

`schemas/side-effect-review-record.schema.json`

Fields:

- `effect_id`
- `packet_id`
- `review_decision`: `approved`, `denied`, `modified`, `needs_human`
- `reviewer_type`: `main_agent`, `human`, `policy`
- `reviewed_at`
- `execution_status`: `not_executed`, `executed`, `failed`
- `authority_tool`
- `result_digest` or `result_ref`, not raw result

This closes the known gap around acceptance/rejection tracking while preserving proposal purity.

### P0: Policy-origin validation

Add a policy validator that rejects trust/security labels from untrusted origins.

Rules:

- `trust_model: measured` requires measured exposure evidence and a trusted verifier ID.
- `review_required` cannot be false when side effects exist.
- `risk` can be escalated by policy but not downgraded by local lane.
- local/client metadata cannot set `policy_tags`, `budget_tags`, or `authority_tags`.

### P1: Lane health schema

Add a small optional schema for local-lane health. This helps Hermes avoid slow/dead local lanes and lets reports distinguish quality failures from operational failures.

Fields:

- `lane`
- `status`
- `checked_at`
- `latency_ms`
- `last_failure_class`
- `cooldown_until`
- `concurrency_limit`

### P1: Guardrail event schema

Add `schemas/guardrail-event.schema.json` and optional `applied_policies` on review packets or telemetry.

Fields:

- `policy_id`
- `stage`: `pre_local`, `post_local`, `pre_authority`, `post_authority`
- `status`: `passed`, `intervened`, `failed_to_respond`, `not_run`
- `duration_ms`
- `masked_entity_counts`

No raw prompt, response, or blocked text.

### P1: Exposure budget policy

Add a policy object for exposure/cost/latency budgets. This is where Sovereignty can improve on gateway budgets by budgeting privacy exposure rather than only dollars.

Example:

```json
{
  "max_cloud_exposure_classification": "summary",
  "max_exposed_tokens_estimated": 1000,
  "max_unmeasured_packets_per_day": 10,
  "require_measured_for_claims": true
}
```

### P1: Attestation/signature spike

Prototype JWS signing of packet digests and side-effect proposal digests. Do not block v0.1 on it, but it is the most differentiated hardening idea from LiteLLM's MCP zero-trust design.

### P2: Shadow-lane evaluation harness

Add a Hermes example that mirrors local prep to a shadow local lane and records quality/latency metadata without changing the authoritative answer.

### P2: Local references / retrieval handles

Add a safe pattern for local-only omitted context handles. Make cloud retrieval require explicit authority policy and update exposure telemetry when retrieval occurs.

## What not to copy

Do not copy these LiteLLM layers into Sovereignty core:

- provider gateway API compatibility;
- full model list routing;
- virtual key server;
- admin dashboard;
- budget database;
- provider-specific parameter normalization;
- generic proxy pass-through;
- enterprise team UI.

Those are gateway responsibilities. Sovereignty should instead define compact contracts that can plug into LiteLLM, Hermes, Portkey, RouteLLM, local worker wrappers, or agent frameworks.

## Product positioning update

Current positioning is good: `local models do the prep. your agent keeps authority.`

Potential sharper line after this LiteLLM review:

> Gateways decide where model calls go. Sovereignty decides what local prep is allowed to become.

Or:

> LiteLLM routes model traffic. Sovereignty governs the handoff from private local work to authority-bearing action.

## Immediate next PR suggestion

Title: `feat: add metadata-only packet telemetry schema`

Scope:

- `schemas/packet-telemetry.schema.json`
- `src/sovereignty/telemetry.py`
- tests for success/failure packets and privacy rejection
- `docs/telemetry.md`
- update Hermes example to emit/validate one telemetry record

Why this first: it directly builds on the Hermes router-packet work, supports the effectiveness report, and gives Sovereignty a concrete artifact that improves on generic gateway logging by being privacy-first and authority-aware.
