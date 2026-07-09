# Consuming Sovereignty contracts from private routers

Sovereignty publishes protocol contracts. A private router may consume those contracts, but it should not publish its live wiring as proof of the protocol.

The working rule is boring and strict: export metadata-only packets that another runtime can validate, keep implementation details private, and make side effects reviewable before any authority-bearing actor executes them.

## Install

Use the public package in consumers that do not need repository internals:

```bash
python3 -m pip install sovereignty-protocol
python3 -c "import sovereignty; print(sovereignty.__version__)"
sovereignty --help
```

For development against a checkout:

```bash
python3 -m pip install -e '.[dev]'
```

The PyPI distribution is `sovereignty-protocol`. The import package and CLI command are both `sovereignty`.

## Validate review packets

A private local-prep lane should emit a compact review packet before the main agent or human acts:

```python
from sovereignty import ReviewPacket, Exposure, validate_packet_dict

packet = ReviewPacket(
    packet_id="pkt_public_example_1",
    lane="contract_review",
    action="summarize_validation_result",
    local_output={"summary": "Metadata-only recommendation."},
    model_metadata={
        "provider": "example-provider",
        "model": "example-model-small",
        "worker_profile": "contract-reviewer",
    },
    exposure=Exposure(
        classification="summary",
        trust_model="measured",
        evidence={"report_id": "measured-exposure-report-example", "metadata_only": True},
    ),
    side_effects=[],
    review_required=False,
)

validated = validate_packet_dict(packet.to_dict())
```

The CLI can validate a serialized packet:

```bash
sovereignty validate examples/contracts/review-packet.json
```

## Validate broker decisions

A private execution broker may choose among already-policy-eligible backend candidates, but the public broker decision is still metadata-only and shadow-safe. It records the decision path; it does not execute a model call or authorize side effects.

```python
from sovereignty.broker_decision import validate_broker_decision_dict

validated = validate_broker_decision_dict(decision_dict)
```

CLI validation:

```bash
sovereignty validate --schema broker-decision examples/contracts/broker-decision-price-selected.json
```

## Export metadata-only evidence

Good public evidence includes:

- schema version and stable public IDs;
- lane/action names that describe capability without revealing live wiring;
- measured exposure classification and digests;
- token/count/latency/cost estimates where they are aggregate and non-sensitive;
- side-effect proposals that remain pending review;
- broker candidates with sanitized backend labels and reason codes.

Do not export raw prompts, raw completions, request bodies, response bodies, worker stdout/stderr, provider account details, local endpoints, provider base URLs, host paths, secrets, private telemetry streams, or live lane maps.

## Public fixtures

Sanitized JSON fixtures live in `examples/contracts/`. They are intended to be small golden examples for non-Python consumers and private-router dogfooding:

- `exposure.json`
- `side-effect-proposal.json`
- `review-packet.json`
- `measured-exposure-report.json`
- `packet-telemetry.json`
- `side-effect-review-record.json`
- `policy.json`
- `guardrail-event.json`
- `lane-health.json`
- `exposure-budget.json`
- broker-decision path fixtures

Validate them with the test suite:

```bash
python -m pytest tests/test_json_schemas.py -q
```

## Dogfood loop for private router-core

When dogfooding a private router against Sovereignty:

1. Generate review packets, telemetry, measured exposure reports, and broker decisions from the private implementation.
2. Strip private details at the router boundary, before writing public fixtures or logs.
3. Validate the exported JSON against Sovereignty schemas or reference validators.
4. If validation fails, fix the narrow public contract or the private exporter. Do not dump router internals into the public repo to make a fixture pass.
5. Publish only sanitized examples and docs.

For broker decisions, older or private router implementations may have an internal shape that is close but not contract-clean. The public exporter should adapt that internal shape before validation:

- add public envelope fields such as `schema_version`, `decision_id`, `packet_id`, `authority_level`, `exposure_origin`, `exposure_state`, `validator_required`, `validator_pass`, `budget`, and `privacy`;
- convert implementation-local price fields into `estimated_cost_usd` for the packet being decided;
- include each candidate's `privacy_class` and `authority_class` from the private registry, but not the registry itself;
- use public reason codes and stage names only;
- omit rejected-candidate summaries if they duplicate the richer `candidates` array or use private-only fields;
- keep `executed` false.

If a field is useful only because of this host's live setup, it is probably private router-core state, not public Sovereignty protocol.
