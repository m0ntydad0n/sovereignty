# Sovereignty

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

Early v0.1 scaffold. The current goal is a small, falsifiable core: schema, policy checks, metadata redaction, a sober threat model, and one Hermes adapter example.

## Repository layout

```text
sovereignty/
  SPEC.md                 # Local-prep / cloud-authority protocol
  THREAT_MODEL.md         # Assumptions, non-goals, failure modes
  docs/measured-exposure.md # Evidence-backed exposure report shape
  docs/protocol-not-gateway.md # Why this is a protocol, not a gateway
  docs/release-checklist.md # v0.1.0 package/release checklist
  schemas/                # Language-agnostic JSON Schema contracts
  src/sovereignty/        # Reference Python implementation
  examples/hermes/        # Hermes local-router adapter examples
  tests/                  # Contract tests
```

## Design principles

1. Local models can prepare. They do not decide.
2. Side effects require main-agent or human authority.
3. Exposure accounting must state whether it is measured or caller-attested.
4. Review packets are structured, versioned, and validated.
5. Privacy/security claims should be falsifiable, not vibes.

## Quick start

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest tests -q
```

The PyPI distribution name is `sovereignty-protocol` because `sovereignty` is already taken on PyPI. The import package and CLI command remain `sovereignty`.

Install from a local checkout:

```bash
python3 -m pip install -e .
sovereignty --help
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

The local-router integration demonstrates a local prep lane producing a review packet with measured exposure evidence and a review-only side-effect proposal for the main Hermes agent.

Validate a packet JSON file:

```bash
sovereignty validate packet.json
```

Redact model metadata:

```bash
sovereignty redact metadata.json
```

## CLI

Sovereignty's first CLI commands are protocol utilities, not router commands:

- `validate packet.json` validates a review packet and returns a JSON status object.
- `redact metadata.json` removes secrets, host-local URLs, and private paths from model metadata.

## JSON Schema contracts

Language-agnostic schemas live in `schemas/`:

- `schemas/review-packet.schema.json`
- `schemas/exposure.schema.json`
- `schemas/measured-exposure-report.schema.json`
- `schemas/side-effect-proposal.schema.json`

These schemas mirror the v0.1 protocol surface for non-Python validators and integrations.

## Release path

The v0.1.0 release checklist lives at `docs/release-checklist.md`. `python -m build` is part of CI, and the package is published under the distribution name `sovereignty-protocol` while preserving the `sovereignty` import package and CLI.

## License

Apache-2.0. Sovereignty is intended to remain open source.
