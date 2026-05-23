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

Sovereignty is not an LLM gateway. It is a contract for local-prep / cloud-authority workflows:

- local lanes produce structured review packets;
- local lanes do not invoke side-effecting tools;
- model and lane metadata is redacted before it leaves the local boundary;
- cloud exposure claims are explicit about their trust model;
- callers can validate packets and policies before a main agent acts.

## Status

Early v0.1 scaffold. The current goal is a small, falsifiable core: schema, policy checks, metadata redaction, a sober threat model, and one Hermes adapter example.

## Repository layout

```text
sovereignty/
  SPEC.md                 # Local-prep / cloud-authority protocol
  THREAT_MODEL.md         # Assumptions, non-goals, failure modes
  src/sovereignty/        # Reference Python implementation
  examples/hermes/        # Hermes local-router adapter example
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
.venv/bin/python -m pip install --upgrade pip pytest
.venv/bin/python -m pytest tests -q
```

Create a basic review packet:

```bash
.venv/bin/python examples/basic_packet.py
```

Validate a packet JSON file:

```bash
PYTHONPATH=src .venv/bin/python -m sovereignty validate packet.json
```

Redact model metadata:

```bash
PYTHONPATH=src .venv/bin/python -m sovereignty redact metadata.json
```

## CLI

Sovereignty's first CLI commands are protocol utilities, not router commands:

- `validate packet.json` validates a review packet and returns a JSON status object.
- `redact metadata.json` removes secrets, host-local URLs, and private paths from model metadata.

## License

Apache-2.0. Sovereignty is intended to remain open source.
