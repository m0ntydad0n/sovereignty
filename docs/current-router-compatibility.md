# Current Hermes router compatibility

This note pins Sovereignty v0.1 to the live local-router shape currently used by the Hermes stack, without publishing private host paths, endpoints, tokens, raw prompts, or process details.

Sovereignty remains the public protocol. Hermes `local_llm_router` remains one adapter. The adapter turns local-router output into a Sovereignty `ReviewPacket`, optional `PacketTelemetry`, and authority-side review records.

## Current live lane map

The public adapter should treat these as sanitized operational identities, not as network configuration:

| Router action | Local prep lane / model | Sovereignty role |
|---|---|---|
| route / classify / extract | local-extractor / llama3.2:3b | routing, sensitivity classification, and structured extraction scout output |
| thread-packet | local-extractor / llama3.2:3b | compact local thread review packet before cloud/main review |
| draft | local-writer / qwen3-coder-local | draft variants from supplied facts only |
| code_plan / code_review / traceback | local-coder / qwen3-coder-local | code triage, review scout, and implementation-plan prep |

Local lanes prepare. They do not send Slack messages, create GitHub issues, deploy, publish, trade, pay, order, or otherwise perform side effects. Any side effect must remain a proposal until a main Hermes/cloud agent or human authority reviews policy and acts.

## Tool-result fields the adapter should preserve

A current Hermes local-router result can include these non-secret fields:

- `packet_id`: metadata-only router packet identifier.
- `worker_profile`: sanitized lane name such as `local-extractor`, `local-writer`, or `local-coder`.
- `model_used`: sanitized model metadata: `profile`, `provider`, `model`, and optional `context_length` only.
- `lane_model_map`: sanitized map from router actions to lane/model labels.
- `raw_context_seen_by_cloud`: telemetry hint that distinguishes cloud-planner calls from pre-cloud/local-ingress calls.

Do not include provider base URLs, local endpoints, host paths, API keys, tokens, raw prompts, stdout/stderr previews, raw worker outputs, or process details in public packets or docs.

## Exposure and savings semantics

`raw_context_seen_by_cloud=false` is the important pre-cloud/local-ingress signal. It means raw local context was withheld from the cloud/main reviewer and only compact local output crossed the boundary.

When `raw_context_seen_by_cloud=false`, the adapter may report `actual_avoided_cloud_tokens` as a strict avoided-exposure floor, computed from raw local input tokens minus compact local output tokens.

When `raw_context_seen_by_cloud` is true or omitted, local-router output may still be useful, but savings are potential savings only because the cloud planner already saw or generated the tool argument text. Do not present potential savings as actual privacy proof.

The operational command center also tracks windowed workload movement. Its dashboard language should stay explicit:

- router-era saved
- 24h saved
- 7d saved
- local_worker_tokens
- router_era_frontier_tokens

These windowed metrics are operational workload estimates, not provider billing truth. `router_era_frontier_tokens` and the related frontier avoided workload view are useful for directionality, but the strict privacy/auditable floor remains packet/pre-cloud evidence such as `actual_avoided_cloud_tokens`.

## Mapping to Sovereignty objects

- Hermes tool result -> `ReviewPacket.model_metadata` with sanitized `worker_profile`, `model_used`, and `lane_model_map`.
- Hermes compact output -> `ReviewPacket.local_output`.
- Pre-cloud/local-ingress accounting -> `PacketTelemetry.token_accounting`.
- Side-effect intent -> review-only side-effect proposal in `ReviewPacket.side_effects`.
- Main Hermes/cloud action -> outside the local lane, under authority-bearing tool policy.

The runnable example at `examples/hermes/local_router_review_packet.py` is the compatibility fixture for this note.
