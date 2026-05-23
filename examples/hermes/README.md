# Hermes adapter example

This directory demonstrates how the current Hermes `local_llm_router` shape can be adapted to Sovereignty.

The core idea is simple:

1. Hermes or another main agent chooses a local prep action.
2. A local worker runs without side-effect authority.
3. The adapter wraps the result in a Sovereignty `ReviewPacket`.
4. The main agent reviews the packet before answering or acting.

This is an adapter example, not the core product. The core product is the packet/policy contract in `src/sovereignty/` and `SPEC.md`.
