# Hermes adapter example

This directory demonstrates how the current Hermes `local_llm_router` shape can be adapted to Sovereignty.

The core idea is simple:

1. Hermes or another main agent chooses a local prep action.
2. A local worker runs without side-effect authority.
3. The adapter wraps the result in a Sovereignty `ReviewPacket`.
4. The main agent reviews the packet before answering or acting.

This is an adapter example, not the core product. The core product is the packet/policy contract in `src/sovereignty/` and `SPEC.md`.

## Runnable local-router integration

`local_router_review_packet.py` is a runnable local-router integration example that does not depend on private Hermes config, local base URLs, tokens, or host paths.

It demonstrates:

- a local prep lane inspecting raw context and returning a `ReviewPacket`;
- the current live lane map: route / classify / extract and thread-packet on local-extractor / llama3.2:3b, draft on local-writer / qwen3-coder-local, and code_plan / code_review / traceback on local-coder / qwen3-coder-local;
- current Hermes tool metadata including sanitized `worker_profile`, `model_used`, `lane_model_map`, and `raw_context_seen_by_cloud=false`;
- a main Hermes agent reviewing the packet before any side effect;
- exposure classification with `trust_model="measured"`;
- strict `actual_avoided_cloud_tokens` accounting only for pre-cloud/local-ingress flows, with potential savings kept separate;
- operational dashboard metric names such as router-era saved, 24h saved, 7d saved, `local_worker_tokens`, and `router_era_frontier_tokens`;
- a strict review-only side-effect proposal for creating an issue;
- a `RecordingBoundary` measured exposure report attached beside the packet;
- metadata-only packet telemetry that references the packet without logging raw context or local output.

Run it from the repository root:

```bash
PYTHONPATH=src python examples/hermes/local_router_review_packet.py
```

In a real Hermes deployment, replace the local `local_prep_lane()` stub with a safe call to a local-router worker such as extraction, classification, code triage, or draft generation. Keep the same authority boundary: the local lane prepares and proposes; the main Hermes/cloud agent validates and decides.
