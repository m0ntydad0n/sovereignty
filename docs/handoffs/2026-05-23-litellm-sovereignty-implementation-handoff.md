# LiteLLM-Inspired Sovereignty Implementation Handoff

> For the next Hermes session: load `hermes-local-llm-routing`, `writing-plans`, and `test-driven-development` skills before implementing. Use strict RED-GREEN-REFACTOR. Do not implement production code before a failing test.

Date: 2026-05-23
Repo: `/Users/monty/projects/sovereignty`
GitHub: `https://github.com/m0ntydad0n/sovereignty`
License: Apache-2.0
Current branch: `main`
Current test command: `.venv/bin/python -m pytest tests -q`
Current baseline: 43 passing tests

## Goal

Design and implement the LiteLLM-inspired operational layer for Sovereignty while preserving the core positioning:

- Sovereignty is not a gateway.
- Sovereignty is a local-prep / cloud-authority protocol.
- Local lanes produce structured review packets.
- Main agents or humans retain authority over final answers and side effects.
- Telemetry must be metadata-only by default; never log raw prompts, local outputs, credentials, private paths, local base URLs, or tool stdout/stderr.

The deep-dive memo to use as the source of truth is:

`docs/litellm-lessons-for-sovereignty.md`

## Current repository state

Relevant existing files:

- `SPEC.md` — protocol spec.
- `README.md` — public framing and quickstart.
- `THREAT_MODEL.md` — current threat model.
- `docs/protocol-not-gateway.md` — positioning against gateways such as LiteLLM.
- `docs/measured-exposure.md` — measured exposure design.
- `docs/litellm-lessons-for-sovereignty.md` — new research memo from LiteLLM docs.
- `schemas/review-packet.schema.json`
- `schemas/exposure.schema.json`
- `schemas/measured-exposure-report.schema.json`
- `schemas/side-effect-proposal.schema.json`
- `src/sovereignty/packet.py`
- `src/sovereignty/measured_exposure.py`
- `src/sovereignty/redaction.py`
- `src/sovereignty/side_effects.py`
- `tests/test_json_schemas.py`
- `tests/test_recording_boundary.py`
- `tests/test_hermes_local_router_example.py`

Current dirty files at handoff time:

- `docs/litellm-lessons-for-sovereignty.md` — untracked research memo.
- This handoff file — untracked when created.

Before implementation, run:

```bash
cd /Users/monty/projects/sovereignty
git status --short
git log --oneline -5
.venv/bin/python -m pytest tests -q
```

Expected baseline at handoff:

```text
43 passed
```

If the research memo or this handoff are still untracked, commit documentation first before feature work:

```bash
git add docs/litellm-lessons-for-sovereignty.md docs/handoffs/2026-05-23-litellm-sovereignty-implementation-handoff.md
git commit -m "docs: add LiteLLM lessons and implementation handoff"
```

## Source research summary

LiteLLM docs reviewed from local clone `/tmp/litellm_docs_repo`:

- routing and load balancing
- per-key/per-team/global router settings
- virtual keys and spend tracking
- team/provider/model/tag budgets
- health-check routing
- retries/cooldowns/fallbacks
- guardrail lifecycle and guardrail policies
- standard logging payload
- log scrubbing / redaction
- rejection of client-side metadata tags
- caching and prompt compression
- custom pricing / zero-cost local models
- traffic mirroring
- MCP zero-trust JWT signing

Extracted themes for Sovereignty:

1. Identity-scoped policy resolution.
2. Metadata-only packet telemetry.
3. Side-effect review lifecycle separate from side-effect proposal.
4. Policy-origin validation: client/local metadata cannot grant trust.
5. Guardrail events across local and authority stages.
6. Lane health records for local runtimes.
7. Exposure budgets rather than only dollar budgets.
8. Optional signed attestation of packet/proposal digests.
9. Shadow-lane evaluation.
10. Local references / retrieval handles with explicit exposure updates.

## Non-negotiable constraints

- Do not turn Sovereignty into LiteLLM, Portkey, RouteLLM, or any generic model gateway.
- Do not add provider-routing API compatibility as core functionality.
- Do not create a virtual-key server, admin dashboard, budget database, or model gateway proxy.
- Do not log raw prompts, raw local model outputs, raw request/response bodies, API keys, bearer tokens, private local paths, host-local URLs, local base URLs, stdout/stderr, or unredacted tracebacks.
- Do not allow local lanes to mark side effects approved/executed.
- Do not allow local/client metadata to promote trust model, policy tags, authority tags, or budget tags.
- Keep schemas language-agnostic and strict with `additionalProperties: false` unless there is a deliberate extension slot.
- Use TDD. For every new public contract, write schema tests and Python tests first, verify RED, then implement minimal GREEN.

## Recommended implementation sequence

Implement as small PR-sized commits. Suggested commit split:

1. `docs: add LiteLLM lessons and implementation handoff`
2. `feat: add metadata-only packet telemetry schema`
3. `feat: add side-effect review records`
4. `feat: add policy-origin validation`
5. `feat: add guardrail event and lane health contracts`
6. `feat: add exposure budget policy contract`
7. `docs: describe signed attestations and shadow evaluation roadmap`

Do not do the JWS attestation implementation unless the earlier contracts are green and small enough to keep the PR coherent. It can be a design doc first.

---

# Phase 0 — Documentation commit

## Task 0.1: Commit the research memo and handoff

Objective: Preserve the research and this execution handoff before code changes.

Files:

- Add: `docs/litellm-lessons-for-sovereignty.md`
- Add: `docs/handoffs/2026-05-23-litellm-sovereignty-implementation-handoff.md`

Commands:

```bash
cd /Users/monty/projects/sovereignty
git status --short
.venv/bin/python -m pytest tests -q
git add docs/litellm-lessons-for-sovereignty.md docs/handoffs/2026-05-23-litellm-sovereignty-implementation-handoff.md
git commit -m "docs: add LiteLLM lessons and implementation handoff"
```

Expected:

- Tests pass before commit.
- Commit contains only docs.

---

# Phase 1 — Packet telemetry schema and Python API

## Design

Add a metadata-only telemetry object for each local-prep run / review packet. This standardizes Hermes `router_packets.jsonl` style records into a reusable Sovereignty protocol contract.

New files:

- `schemas/packet-telemetry.schema.json`
- `src/sovereignty/telemetry.py`
- `docs/telemetry.md`
- `tests/test_packet_telemetry.py`

Modify:

- `src/sovereignty/__init__.py`
- `tests/test_json_schemas.py`
- `README.md` or `SPEC.md` only if needed to link docs.

Telemetry fields:

Required:

- `schema_version`: const `0.1`
- `run_id`: nonempty string
- `packet_id`: nonempty string
- `trace_id`: nonempty string
- `adapter`: nonempty string, e.g. `hermes-local-router`
- `lane`: nonempty string
- `action`: nonempty string
- `status`: enum `success`, `failure`, `timeout`, `policy_blocked`
- `status_fields`: object
- `timing`: object
- `token_accounting`: object
- `privacy`: object

Optional:

- `consumer_session_id`
- `cost_accounting`
- `error`

Status fields:

- `local_lane_status`: enum `success`, `failure`, `timeout`, `not_run`
- `guardrail_status`: enum `success`, `guardrail_intervened`, `guardrail_failed_to_respond`, `not_run`
- `exposure_status`: enum `measured`, `caller_attested`, `not_applicable`, `unknown`
- `side_effect_status`: enum `proposed_none`, `proposed_pending_review`, `reviewed`, `blocked`, `not_applicable`

Timing:

- `started_at`: string date-time
- `ended_at`: string date-time or null
- `duration_ms`: number >= 0 or null

Token accounting:

- `raw_input_tokens_estimated`: integer >= 0
- `local_output_tokens_estimated`: integer >= 0
- `exposed_to_cloud_tokens_estimated`: integer >= 0
- `kept_local_tokens_estimated`: integer >= 0

Privacy:

- `metadata_only`: const true
- `raw_payload_logged`: const false
- `local_output_logged`: const false

Error:

- `error_class`: nonempty string
- `error_message_digest`: optional `sha256:<64 hex>`
- no raw traceback by default.

Forbidden anywhere in telemetry:

- `messages`
- `response`
- `prompt`
- `completion`
- `stdout`
- `stderr`
- `raw_input`
- `raw_output`
- `request_body`
- `response_body`
- `api_key`
- `token`
- `secret`
- `password`
- `base_url`
- `endpoint`
- `path`

## Task 1.1: Write RED schema tests

Objective: Add failing tests that require the new packet telemetry schema and privacy constraints.

File: `tests/test_packet_telemetry.py`

Add tests:

```python
def test_valid_packet_telemetry_schema_accepts_metadata_only_record():
    # Load schemas/packet-telemetry.schema.json.
    # Validate a complete success telemetry record.
```

```python
def test_packet_telemetry_rejects_raw_prompt_and_response_fields():
    # Start from valid telemetry.
    # Add fields like messages, response, stdout, raw_input.
    # Validate each fails.
```

```python
def test_packet_telemetry_rejects_secret_or_private_metadata_keys():
    # Add api_key/base_url/path under model_metadata or adapter_metadata if such extension exists.
    # Validate failure.
```

```python
def test_packet_telemetry_accepts_failure_without_raw_traceback():
    # status=failure, error_class only, optional digest.
```

Run:

```bash
.venv/bin/python -m pytest tests/test_packet_telemetry.py -q
```

Expected RED:

- Fails because `schemas/packet-telemetry.schema.json` does not exist.

## Task 1.2: Add minimal packet telemetry schema

Objective: Make schema tests pass with strict metadata-only validation.

Create: `schemas/packet-telemetry.schema.json`

Implementation notes:

- Use JSON Schema draft 2020-12.
- `additionalProperties: false` at top level and for nested objects.
- Use `propertyNames.not.pattern` to reject forbidden raw fields where extension objects exist.
- Prefer explicit fields over broad extension maps.

Run:

```bash
.venv/bin/python -m pytest tests/test_packet_telemetry.py -q
```

Expected GREEN:

- New packet telemetry tests pass.

## Task 1.3: Add Python telemetry dataclass/helpers with RED tests

Objective: Provide Python API to construct and validate telemetry records.

File: `tests/test_packet_telemetry.py`

Add RED tests for:

- `PacketTelemetry(...).to_dict()` returns schema-valid dict.
- `PacketTelemetry.from_dict(valid_dict)` validates and round-trips.
- Creating telemetry with raw field names in metadata raises `SovereigntyPolicyError`.
- `build_error_digest("...")` returns `sha256:<64 hex>` and does not expose raw message.

Create: `src/sovereignty/telemetry.py`

Suggested API:

```python
@dataclass
class PacketTelemetry:
    run_id: str
    packet_id: str
    trace_id: str
    adapter: str
    lane: str
    action: str
    status: str
    status_fields: dict[str, Any]
    timing: dict[str, Any]
    token_accounting: dict[str, int]
    privacy: dict[str, bool] = field(default_factory=default_privacy)
    consumer_session_id: str | None = None
    cost_accounting: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    schema_version: str = "0.1"
```

Validation:

- Required strings nonempty.
- Privacy constants enforced.
- Token counts nonnegative integers.
- Reject forbidden raw field names recursively.
- Reuse `SovereigntyPolicyError`.

Run:

```bash
.venv/bin/python -m pytest tests/test_packet_telemetry.py -q
.venv/bin/python -m pytest tests -q
```

Commit:

```bash
git add schemas/packet-telemetry.schema.json src/sovereignty/telemetry.py tests/test_packet_telemetry.py src/sovereignty/__init__.py
git commit -m "feat: add metadata-only packet telemetry contract"
```

## Task 1.4: Add telemetry docs

Create: `docs/telemetry.md`

Must cover:

- Why telemetry is metadata-only.
- Difference from gateway request/response logging.
- Required fields.
- Privacy guarantees.
- Error handling.
- Hermes router packet mapping.
- Example success and failure records.

Add doc contract tests if style matches existing docs tests.

Run full tests and commit:

```bash
.venv/bin/python -m pytest tests -q
git add docs/telemetry.md README.md SPEC.md tests/test_*telemetry*.py
git commit -m "docs: document packet telemetry contract"
```

---

# Phase 2 — Side-effect review records

## Design

Current `side-effect-proposal.schema.json` is intentionally review-only. Do not add approval/execution fields to it. Add a separate authority-side review record.

New files:

- `schemas/side-effect-review-record.schema.json`
- `src/sovereignty/side_effect_review.py`
- `docs/side-effect-review.md` or add section to existing side-effect docs if present.
- `tests/test_side_effect_review.py`

Required fields:

- `schema_version`: const `0.1`
- `review_id`: nonempty string
- `packet_id`: nonempty string
- `effect_id`: nonempty string
- `review_decision`: enum `approved`, `denied`, `modified`, `needs_human`
- `reviewer_type`: enum `main_agent`, `human`, `policy`
- `reviewed_at`: date-time string
- `execution_status`: enum `not_executed`, `executed`, `failed`

Optional fields:

- `authority_tool`
- `modified_payload_digest`
- `result_digest`
- `result_ref`
- `notes_digest`

No raw result or payload by default.

## Task 2.1: RED tests for review record schema

Tests:

- Valid approved/not_executed review record passes.
- Valid denied/not_executed review record passes.
- Raw `result`, `execution_result`, `payload`, `approved_by`, `executed_at` fields fail.
- Missing required fields fail.
- Invalid enum values fail.

Run expected RED:

```bash
.venv/bin/python -m pytest tests/test_side_effect_review.py -q
```

## Task 2.2: Implement schema and Python helper

Create schema and `SideEffectReviewRecord` dataclass.

Validation:

- Nonempty required IDs.
- Digests match `sha256:<64 hex>` when present.
- Reject raw/execution content fields not in schema.

Run:

```bash
.venv/bin/python -m pytest tests/test_side_effect_review.py -q
.venv/bin/python -m pytest tests -q
```

Commit:

```bash
git add schemas/side-effect-review-record.schema.json src/sovereignty/side_effect_review.py tests/test_side_effect_review.py src/sovereignty/__init__.py
git commit -m "feat: add side-effect review record contract"
```

---

# Phase 3 — Policy-origin validation

## Design

Add policy validation that distinguishes local/client metadata from authority/verifier metadata. LiteLLM rejects client-side metadata tags that influence routing/budgets. Sovereignty should reject local/client-provided labels that influence trust or authority.

New files:

- `schemas/policy.schema.json`
- `src/sovereignty/policies.py` or extend `src/sovereignty/policy.py`
- `tests/test_policy_validation.py`
- `docs/policy.md`

Concepts:

- Policy tags: trusted labels that affect review, exposure, budget, or authority.
- Metadata origin: `caller`, `local_lane`, `authority`, `verifier`.
- Trusted verifier IDs for measured exposure.
- Max cloud exposure class.
- Risk escalation only.

Suggested policy fields:

```json
{
  "schema_version": "0.1",
  "policy_id": "default-local-prep",
  "trusted_verifier_ids": ["sovereignty.recording_proxy.v0"],
  "max_cloud_exposure_classification": "summary",
  "require_measured_exposure_for_privacy_claims": true,
  "trusted_metadata_origins": ["authority", "verifier"],
  "forbidden_client_metadata_keys": ["policy_tags", "budget_tags", "authority_tags", "trust_tags"],
  "forbidden_side_effect_types": ["deploy", "trade", "payment"],
  "risk_floor_by_effect_type": {"send_message": "medium", "deploy": "high"}
}
```

## Task 3.1: RED tests for policy-origin validation

Tests:

- `trust_model=measured` with untrusted `verifier_id` fails.
- `trust_model=measured` with trusted verifier and valid evidence passes.
- local/client metadata containing `policy_tags`, `budget_tags`, `authority_tags`, or `trust_tags` fails.
- risk downgrade attempt fails or is escalated to floor.
- forbidden side-effect type fails.
- policy allows packet with summary exposure and no side effects.

## Task 3.2: Implement policy validator

Suggested API:

```python
@dataclass
class SovereigntyPolicy:
    policy_id: str
    trusted_verifier_ids: set[str]
    max_cloud_exposure_classification: str = "summary"
    forbidden_client_metadata_keys: tuple[str, ...] = (...)
    forbidden_side_effect_types: tuple[str, ...] = (...)
    risk_floor_by_effect_type: dict[str, str] = field(default_factory=dict)

    def validate_packet(self, packet: ReviewPacket, *, metadata_origin: str = "local_lane") -> ReviewPacket:
        ...
```

Implementation notes:

- Do not mutate packet except optional risk escalation if tests choose escalation behavior.
- Prefer failing closed for untrusted origins.
- Keep policy separate from packet core validation.

Run full suite and commit:

```bash
.venv/bin/python -m pytest tests -q
git add schemas/policy.schema.json src/sovereignty/policy.py tests/test_policy_validation.py docs/policy.md
git commit -m "feat: add policy-origin validation"
```

---

# Phase 4 — Guardrail events and lane health

## Design

Add optional metadata objects for operational maturity without requiring a gateway.

New schemas:

- `schemas/guardrail-event.schema.json`
- `schemas/lane-health.schema.json`

New Python modules:

- `src/sovereignty/guardrails.py`
- `src/sovereignty/lane_health.py`

Tests:

- `tests/test_guardrail_events.py`
- `tests/test_lane_health.py`

## Guardrail event schema

Required:

- `schema_version`: `0.1`
- `event_id`
- `policy_id`
- `stage`: `pre_local`, `post_local`, `pre_authority`, `post_authority`
- `status`: `passed`, `intervened`, `failed_to_respond`, `not_run`
- `started_at`
- `ended_at`
- `duration_ms`

Optional:

- `guardrail_name`
- `masked_entity_counts`: object of string -> nonnegative int
- `intervention_type`: enum `none`, `blocked`, `modified`, `escalated`

Forbidden:

- raw blocked text
- raw prompt
- raw response
- request body
- response body

## Lane health schema

Required:

- `schema_version`: `0.1`
- `lane`
- `status`: `healthy`, `degraded`, `cooldown`, `unavailable`
- `checked_at`

Optional:

- `latency_ms`
- `last_success_at`
- `last_failure_class`
- `cooldown_until`
- `concurrency_limit`

## Tasks

Follow same RED/GREEN pattern:

1. Write schema tests that fail due to missing files.
2. Add schemas.
3. Add Python dataclasses/helpers.
4. Add docs section or `docs/operations.md`.
5. Run full suite.
6. Commit.

Suggested commit:

```bash
git add schemas/guardrail-event.schema.json schemas/lane-health.schema.json src/sovereignty/guardrails.py src/sovereignty/lane_health.py tests/test_guardrail_events.py tests/test_lane_health.py docs/operations.md
git commit -m "feat: add guardrail event and lane health contracts"
```

---

# Phase 5 — Exposure budget policy

## Design

Adapt LiteLLM's budget discipline into Sovereignty-specific privacy and authority budgets.

New schema:

- `schemas/exposure-budget.schema.json`

New module:

- `src/sovereignty/exposure_budget.py`

Required fields:

- `schema_version`: `0.1`
- `budget_id`
- `max_cloud_exposure_classification`

Optional fields:

- `max_exposed_tokens_estimated`
- `max_raw_cloud_tokens_per_run`
- `max_unmeasured_packets_per_day`
- `max_side_effect_proposals_per_packet`
- `max_local_latency_ms`
- `require_measured_for_privacy_claims`

Validation behavior:

- Classification order: `none < summary < excerpt < raw`; `unknown` should fail closed unless explicitly allowed.
- A packet with exposure above budget fails.
- Telemetry with exposed tokens above budget fails.
- Too many side effects fails.
- Measured-required but caller-attested exposure fails.

Tests:

- Valid summary packet under budget passes.
- Raw exposure fails when max is summary.
- Unknown exposure fails by default.
- Too many side-effect proposals fails.
- Exposed token count over max fails.

Commit:

```bash
git add schemas/exposure-budget.schema.json src/sovereignty/exposure_budget.py tests/test_exposure_budget.py docs/policy.md
git commit -m "feat: add exposure budget policy contract"
```

---

# Phase 6 — Hermes example integration

## Design

Update the Hermes example to show how a local-router adapter can produce:

- Review packet.
- Packet telemetry.
- Optional side-effect review record if authority review occurs.
- No raw prompt/output in telemetry.

Files:

- Modify: `examples/hermes/local_router_review_packet.py`
- Modify: `examples/hermes/README.md`
- Modify or add: `tests/test_hermes_local_router_example.py`

Tests:

- Example returns schema-valid review packet.
- Example returns schema-valid packet telemetry.
- Telemetry references packet ID.
- Telemetry privacy flags are strict.
- No raw input appears in telemetry JSON.

Run:

```bash
.venv/bin/python -m pytest tests/test_hermes_local_router_example.py -q
.venv/bin/python -m pytest tests -q
PYTHONPATH=src .venv/bin/python examples/hermes/local_router_review_packet.py
```

Commit:

```bash
git add examples/hermes/local_router_review_packet.py examples/hermes/README.md tests/test_hermes_local_router_example.py
git commit -m "feat: add telemetry to Hermes local-router example"
```

---

# Phase 7 — Attestation design doc, not full implementation unless time remains

## Design

LiteLLM MCP zero-trust JWT signing is relevant. Sovereignty can later sign packet/proposal digests so authority tools know the proposal passed through a known validator.

For now, create design doc:

- `docs/attestation.md`

Must cover:

- JWS/JWT-style signing of packet digests, not raw packet payloads.
- Fields: issuer, audience, packet_digest, policy_digest, expires_at, key_id, jwks_url.
- What this proves and what it does not prove.
- Key rotation and TTL.
- Threats: replay, stolen signing key, bypassing verifier, forged local packet.
- Integration with side-effect review records.

Add doc contract tests if appropriate.

Commit:

```bash
git add docs/attestation.md tests/test_attestation_docs.py
git commit -m "docs: design packet attestation boundary"
```

---

# Phase 8 — Shadow-lane evaluation design doc

Create:

- `docs/shadow-lane-evaluation.md`

Must cover:

- Shadow local lanes are evaluation-only.
- Shadow output must never affect final answer or side effects.
- Record metadata-only quality/latency comparisons.
- Use for classifier/writer/extractor lane trials.
- Link to packet telemetry and lane health.

Commit:

```bash
git add docs/shadow-lane-evaluation.md tests/test_shadow_lane_docs.py
git commit -m "docs: define shadow-lane evaluation pattern"
```

---

# Acceptance criteria

Implementation is complete when:

- All tests pass: `.venv/bin/python -m pytest tests -q`.
- New schemas exist and are covered by tests:
  - `packet-telemetry.schema.json`
  - `side-effect-review-record.schema.json`
  - `policy.schema.json`
  - `guardrail-event.schema.json`
  - `lane-health.schema.json`
  - `exposure-budget.schema.json`
- Python helpers exist and are covered by tests:
  - telemetry
  - side-effect review
  - policy-origin validation
  - guardrail events
  - lane health
  - exposure budget
- Hermes example emits/validates packet telemetry.
- Docs explain that this is operational protocol hardening, not a gateway.
- No new code stores raw prompts, raw local outputs, request bodies, response bodies, stdout/stderr, secrets, private paths, local URLs, or base URLs.
- Side-effect proposal schema remains review-only and does not contain execution/approval fields.
- Side-effect review record is separate from proposal.
- Commits are small and topic-scoped.

## Verification commands

Run before final handoff:

```bash
cd /Users/monty/projects/sovereignty
.venv/bin/python -m pytest tests -q
python -m build
python -m twine check dist/*
PYTHONPATH=src .venv/bin/python examples/hermes/local_router_review_packet.py
git status --short
git log --oneline -10
```

If `twine` is missing, either install dev dependencies if configured or report that package check was skipped due to missing dependency. Do not claim it passed without running it.

## Suggested final summary format

When done, summarize:

- Commits created.
- Schemas added.
- Python modules added.
- Docs added.
- Tests run and results.
- Privacy/no-raw-data checks.
- Any intentionally deferred items, especially JWS attestation implementation or shadow-lane runtime harness.

## Copy/paste prompt for the next session

Use this exact prompt in a new Hermes session:

```text
We are in /Users/monty/projects/sovereignty. Please design and implement the LiteLLM-inspired Sovereignty operational contracts from docs/handoffs/2026-05-23-litellm-sovereignty-implementation-handoff.md.

Load the hermes-local-llm-routing, writing-plans, and test-driven-development skills first. Follow strict TDD: write failing tests, verify RED, implement minimal GREEN, run full tests, commit in small topic-scoped commits.

Do not turn Sovereignty into a gateway. Keep it a local-prep / cloud-authority protocol. Telemetry and logs must be metadata-only by default and must reject raw prompts, raw local outputs, request/response bodies, stdout/stderr, credentials, private paths, and local base URLs.

Start by committing the docs/litellm-lessons-for-sovereignty.md research memo and this handoff if they are still untracked, then implement Phase 1 packet telemetry schema/API. Continue through the phases as long as the branch remains clean and tests pass.
```
