# Sovereignty Protocol Specification

Version: 0.1-draft

## 1. Purpose

Sovereignty defines a local-prep / cloud-authority contract for AI agents.

A local lane may inspect raw local context and produce a review packet. A main agent or human reviewer may inspect the review packet and decide whether to answer, request more information, or authorize a side effect.

The protocol is intentionally smaller than a model gateway. It does not choose every provider. It defines the handoff boundary between local prep work and authority-bearing agent actions.

## 2. Terms

- Local lane: a local or self-hosted model/tool path used for preparation work.
- Main agent: the authority-bearing agent that can produce user-visible answers or invoke side-effecting tools.
- Side effect: any action that changes external state, sends a message, writes a file, deploys, trades, pays, publishes, or modifies an account/system.
- Review packet: a structured object produced by a local lane for review by a main agent or human.
- Cloud exposure: whether raw input, excerpts, summaries, or no source context were sent to a cloud model/provider.

## 3. Review packet

A Sovereignty review packet MUST include:

- `schema_version`: protocol schema version, e.g. `0.1`
- `packet_id`: stable unique identifier
- `lane`: local lane name
- `action`: local prep action
- `local_output`: structured or textual local result
- `model_metadata`: redacted non-secret model/lane metadata
- `exposure`: exposure statement and trust model
- `side_effects`: proposed side effects, if any
- `review_required`: boolean; MUST be true if any side effect is proposed

A packet MUST NOT include API keys, bearer tokens, local base URLs, absolute private paths, environment variables, or raw secret values in `model_metadata`.

The canonical machine-readable v0.1 contracts are published under `schemas/`:

- `schemas/review-packet.schema.json`
- `schemas/exposure.schema.json`
- `schemas/measured-exposure-report.schema.json`
- `schemas/side-effect-proposal.schema.json`
- `schemas/packet-telemetry.schema.json`
- `schemas/side-effect-review-record.schema.json`

## 4. Packet telemetry

A local-prep run MAY emit packet telemetry beside the review packet. Packet telemetry is metadata-only operational evidence for status, timing, token estimates, privacy flags, and digest-only errors.

Telemetry MUST NOT include raw prompts, local outputs, request or response bodies, stdout/stderr, credentials, private paths, host-local URLs, local base URLs, endpoints, or raw tracebacks.

Packet telemetry does not approve side effects and does not replace exposure evidence. It references the review packet by `packet_id` and records whether exposure was measured, caller-attested, unknown, or not applicable. See `docs/telemetry.md` and `schemas/packet-telemetry.schema.json`.

## 5. Exposure classes

`exposure.classification` MUST be one of:

- `raw`: raw source context reached the cloud/main model
- `excerpt`: only excerpts reached the cloud/main model
- `summary`: only a compact local summary/review packet reached the cloud/main model
- `none`: no source context reached the cloud/main model
- `unknown`: caller cannot assert exposure

`exposure.trust_model` MUST be one of:

- `caller_attested`: the caller asserts this; Sovereignty did not measure egress
- `measured`: an egress verifier or recording proxy measured this
- `not_applicable`

Caller-attested exposure is useful for plumbing but MUST NOT be marketed as proof.

## 6. Side-effect boundary

Local lanes MUST NOT perform side effects. If a local lane believes a side effect is needed, it MUST include a proposed side effect in the review packet and set `review_required` to true.

A proposed side effect MUST be an object with these fields:

- `effect_id`: stable identifier unique within the packet
- `effect_type`: action category, such as `send_message`, `write_file`, `create_issue`, or `deploy`
- `tool`: requested authority-bearing tool or integration
- `intent`: human-readable reason for the proposed action
- `target`: object describing the destination without requiring secrets
- `payload`: object containing the proposed arguments/content for review
- `risk`: one of `low`, `medium`, or `high`

A proposed side effect MUST NOT contain execution or approval state such as `executed_at`, `execution_id`, `execution_result`, `approved_at`, `approved_by`, `result`, or `status`. The main agent or human reviewer is responsible for approving, denying, transforming, or executing proposed side effects under its own tool policy.

Authority-side review metadata belongs in a separate side-effect review record. A review record MAY document `review_decision`, `reviewer_type`, `reviewed_at`, and `execution_status`, plus digest-only references for modified payloads, results, or notes. It MUST NOT add approval or execution fields back into the local-lane proposal object. See `docs/side-effect-review.md` and `schemas/side-effect-review-record.schema.json`.

## 7. Non-goals

Sovereignty is not:

- a replacement for LiteLLM, Portkey, RouteLLM, or provider gateways;
- a sandbox by itself;
- a guarantee that a local model is safe or correct;
- a replacement for human review for high-risk domains.

## 8. Compatibility

Implementations SHOULD be easy to integrate with:

- local model runtimes such as Ollama, llama.cpp, vLLM, and OpenAI-compatible local endpoints;
- agent frameworks and CLIs;
- existing gateways such as LiteLLM as transport layers.

For the positioning rationale and concrete comparison dimensions, see `docs/protocol-not-gateway.md`. Sovereignty is meant to compose with gateways rather than replace their provider-routing, retry, cost, and observability responsibilities.
