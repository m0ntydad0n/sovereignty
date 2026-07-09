# Sovereignty

[![PyPI version](https://img.shields.io/pypi/v/sovereignty-protocol.svg)](https://pypi.org/project/sovereignty-protocol/)
[![Python versions](https://img.shields.io/pypi/pyversions/sovereignty-protocol.svg)](https://pypi.org/project/sovereignty-protocol/)
[![Tests](https://github.com/m0ntydad0n/sovereignty/actions/workflows/tests.yml/badge.svg)](https://github.com/m0ntydad0n/sovereignty/actions/workflows/tests.yml)
[![Release](https://img.shields.io/github/v/release/m0ntydad0n/sovereignty)](https://github.com/m0ntydad0n/sovereignty/releases/tag/v0.1.0)
[![License](https://img.shields.io/github/license/m0ntydad0n/sovereignty)](LICENSE)

```text
                         .-.
                        /___\
                       (|o o|)
                    .--.\_-_/ .--.
                   /  _  '-'  _  \
                  /__/ |     | \__\
                  |  | |     | |  |
                  |__| |_____| |__|
                       /  |  \
                      /___|___\

   ______                               _             __
  / ___/ /___ _   _____  ________  (_)___ _____  / /___  __
  \__ \/ __ \ | / / _ \/ ___/ _ \/ / __ `/ __ \/ __/ / / /
 ___/ / /_/ / |/ /  __/ /  /  __/ / /_/ / / / / /_/ /_/ /
/____/\____/|___/\___/_/   \___/_/\__, /_/ /_/\__/\__, /
                                  /____/          /____/

        local models do the prep. your agent keeps authority.
```

Sovereignty is an open-source protocol and reference implementation for local-first agent delegation. It defines how local model lanes can perform private prep work — classification, extraction, drafting, code triage, and sensitivity checks — while a main agent retains authority over final answers and side effects.

Sovereignty is not an LLM gateway. It is a contract for local-prep / cloud-authority workflows; see `docs/protocol-not-gateway.md` for the design note on why this is a protocol, not a gateway:

- local lanes produce structured review packets;
- local lanes do not invoke side-effecting tools;
- model and lane metadata is redacted before it leaves the local boundary;
- cloud exposure claims are explicit about their trust model;
- measured exposure reports can attach evidence without leaking raw prompts or endpoints;
- proposed side effects use a strict review-only schema before any authority-bearing tool acts;
- callers can validate packets and policies before a main agent acts.

## Status

v0.1.0 protocol release. The public surface is intentionally small and falsifiable: schema contracts, policy checks, metadata redaction, measured exposure reporting, side-effect review boundaries, a sober threat model, and Hermes adapter examples.

Sovereignty is still not a router or gateway. The private router implementation can evolve independently; this repository publishes the boundary contract local-prep systems must satisfy before an authority-bearing agent acts.

## Repository layout

```text
sovereignty/
  SPEC.md                 # Local-prep / cloud-authority protocol
  THREAT_MODEL.md         # Assumptions, non-goals, failure modes
  docs/measured-exposure.md # Evidence-backed exposure report shape
  docs/telemetry.md         # Metadata-only packet telemetry contract
  docs/side-effect-review.md # Authority-side side-effect review records
  docs/policy.md            # Policy-origin validation and exposure/side-effect gates
  docs/operations.md        # Guardrail events and lane health records
  docs/broker-decision.md   # Metadata-only execution broker decision packets
  docs/protocol-not-gateway.md # Why this is a protocol, not a gateway
  docs/public-private-boundary.md # What belongs in public vs private implementations
  docs/current-router-compatibility.md # Current Hermes local-router adapter boundary
  docs/release-checklist.md # v0.1.0 package/release checklist
  schemas/                # Language-agnostic JSON Schema contracts
  src/sovereignty/        # Reference Python implementation
  examples/hermes/        # Hermes local-router adapter examples
  examples/contracts/     # Public JSON contract fixtures
  tests/                  # Contract tests
```

## Design principles

1. Local models can prepare. They do not decide.
2. Side effects require main-agent or human authority.
3. Exposure accounting must state whether it is measured or caller-attested.
4. Review packets are structured, versioned, and validated.
5. Privacy/security claims should be falsifiable, not vibes.

## First public proof

The v0.1 proof is intentionally narrow: a local lane reads raw diagnostic context, emits a compact `ReviewPacket`, attaches measured exposure evidence, and proposes a side effect that remains review-only until the authority-bearing agent acts.

Run it from a checkout:

```bash
PYTHONPATH=src .venv/bin/python examples/hermes/local_router_review_packet.py
```

What to look for in the JSON output:

- `review_packet.local_output` contains the compact local summary, not the raw incident text.
- `review_packet.model_metadata` keeps sanitized `worker_profile`, `model_used`, and `lane_model_map` fields, without base URLs, host paths, or tokens.
- `review_packet.exposure.trust_model` is `measured`, and the attached `measured_exposure_report` avoids raw request bodies.
- `packet_telemetry.token_accounting` separates estimated local/input/output counts from exposed-to-cloud counts.
- `current_router_compatibility.actual_avoided_cloud_tokens` is only claimed for the pre-cloud/local-ingress shape where `raw_context_seen_by_cloud=false`.
- Side effects are proposals only; the local lane cannot create issues, send messages, publish, deploy, trade, pay, or order.

That is the positioning wedge: LiteLLM, Portkey, and RouteLLM are useful gateway/routing layers; Sovereignty is the local-prep / cloud-authority contract around what local workers may prepare, what evidence crosses the boundary, and who is allowed to act.

## Quick start

Install the public protocol package from PyPI:

```bash
python3 -m pip install sovereignty-protocol
python3 -c "import sovereignty; print(sovereignty.__version__)"
sovereignty --help
```

The PyPI distribution name is `sovereignty-protocol` because `sovereignty` is already taken on PyPI. The import package and CLI command remain `sovereignty`.

Install from a local checkout for development:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest tests -q
.venv/bin/sovereignty --help
```

Create a basic review packet:

```bash
.venv/bin/python examples/basic_packet.py
```

Run the measured-exposure recording boundary example:

```bash
.venv/bin/python examples/recording_boundary.py
```

Run the Hermes local-router integration example:

```bash
PYTHONPATH=src .venv/bin/python examples/hermes/local_router_review_packet.py
```

The local-router integration demonstrates a local prep lane producing a review packet with measured exposure evidence, metadata-only packet telemetry, and a review-only side-effect proposal for the main Hermes agent.

Validate a packet JSON file:

```bash
sovereignty validate packet.json
```

Validate a broker decision JSON file:

```bash
sovereignty validate --schema broker-decision examples/contracts/broker-decision-price-selected.json
```

Redact model metadata:

```bash
sovereignty redact metadata.json
```

## CLI

Sovereignty's first CLI commands are protocol utilities, not router commands:

- `validate packet.json` validates a review packet and returns a JSON status object.
- `validate --schema broker-decision broker-decision.json` validates a metadata-only broker decision packet and returns a JSON status object.
- `redact metadata.json` removes secrets, host-local URLs, and private paths from model metadata.

## JSON Schema contracts

Language-agnostic schemas live in `schemas/`:

- `schemas/review-packet.schema.json`
- `schemas/exposure.schema.json`
- `schemas/measured-exposure-report.schema.json`
- `schemas/side-effect-proposal.schema.json`
- `schemas/packet-telemetry.schema.json`
- `schemas/side-effect-review-record.schema.json`
- `schemas/policy.schema.json`
- `schemas/guardrail-event.schema.json`
- `schemas/lane-health.schema.json`
- `schemas/exposure-budget.schema.json`
- `schemas/broker-decision.schema.json`

These schemas mirror the v0.1 protocol surface for non-Python validators and integrations. Packet telemetry is documented in `docs/telemetry.md` and is metadata-only by default. Side-effect review records are documented in `docs/side-effect-review.md` and remain separate from local-lane side-effect proposals. Policy-origin validation and exposure budgets are documented in `docs/policy.md`. Guardrail events and lane health are documented in `docs/operations.md`. Broker decisions are documented in `docs/broker-decision.md`; the public/private boundary is documented in `docs/public-private-boundary.md`.

## Release path

The v0.1.0 release checklist lives at `docs/release-checklist.md`. `python -m build` is part of CI, and the package is published under the distribution name `sovereignty-protocol` while preserving the `sovereignty` import package and CLI.

## License

Apache-2.0. Sovereignty is intended to remain open source.
