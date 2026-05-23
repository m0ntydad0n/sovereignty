# Contributing to Sovereignty

Sovereignty is early. Contributions should keep the project small, falsifiable, and protocol-first.

## Project principles

- Prefer protocol clarity over framework breadth.
- Keep local lanes non-authoritative.
- Treat local outputs as review packets, not final answers.
- Distinguish caller-attested exposure from measured exposure.
- Do not claim safety properties that tests or docs cannot defend.
- Avoid reimplementing full LLM gateway functionality unless it directly supports the local-prep / cloud-authority contract.

## Development setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip pytest
.venv/bin/python -m pytest tests -q
```

## Tests

Every behavior change should include a test. Useful test categories:

- review packet schema validation
- side-effect boundary enforcement
- model metadata redaction
- exposure trust-model semantics
- adapter behavior that preserves the Sovereignty contract

## Security and privacy

Do not include real API keys, bearer tokens, private URLs, customer data, local absolute paths, or raw sensitive documents in issues, tests, fixtures, examples, or docs.

If you find a vulnerability, please open a minimal issue first without secrets or exploit payloads. If the project later needs private disclosure infrastructure, this file will be updated.
