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
- a main Hermes agent reviewing the packet before any side effect;
- exposure classification with `trust_model="measured"`;
- a strict review-only side-effect proposal for creating an issue;
- a `RecordingBoundary` measured exposure report attached beside the packet.

Run it from the repository root:

```bash
PYTHONPATH=src python examples/hermes/local_router_review_packet.py
```

In a real Hermes deployment, replace the local `local_prep_lane()` stub with a safe call to a local-router worker such as extraction, classification, code triage, or draft generation. Keep the same authority boundary: the local lane prepares and proposes; the main Hermes/cloud agent validates and decides.
