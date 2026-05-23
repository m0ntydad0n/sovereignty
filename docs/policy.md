# Policy-origin validation

Sovereignty policy validation distinguishes metadata supplied by low-authority callers/local lanes from metadata supplied by authority or verifier components.

The rule is fail-closed: caller or local-lane metadata cannot grant trust, authority, or budget treatment to itself.

## Policy schema

The canonical policy schema is `schemas/policy.schema.json`.

A v0.1 policy defines:

- `policy_id`: stable policy identifier.
- `trusted_verifier_ids`: verifier IDs allowed to support `trust_model="measured"` exposure claims.
- `max_cloud_exposure_classification`: maximum allowed cloud exposure (`none`, `summary`, `excerpt`, or `raw`).
- `require_measured_exposure_for_privacy_claims`: whether caller-attested exposure is insufficient.
- `trusted_metadata_origins`: currently authority-side origins only: `authority` and `verifier`.
- `forbidden_client_metadata_keys`: keys that callers and local lanes may not provide.
- `forbidden_side_effect_types`: side-effect categories blocked by policy.
- `risk_floor_by_effect_type`: minimum allowed risk labels for effect types.

## Metadata origins

Supported packet-validation origins are:

- `caller`
- `local_lane`
- `authority`
- `verifier`

Only `authority` and `verifier` may be configured as trusted metadata origins. A caller or local lane cannot attach fields such as `policy_tags`, `budget_tags`, `authority_tags`, or `trust_tags` and expect those fields to influence review or budgets.

## Measured exposure verifier IDs

A packet with `exposure.trust_model="measured"` must include evidence with a trusted `verifier_id`:

```json
{
  "classification": "summary",
  "trust_model": "measured",
  "evidence": {
    "verifier_id": "sovereignty.recording_proxy.v0"
  }
}
```

If the verifier ID is missing or untrusted, policy validation fails. If measured exposure is required, caller-attested exposure also fails.

## Side-effect policy

Policy validation can block entire side-effect types such as `deploy`, `trade`, or `payment`.

It can also enforce risk floors. For example, if `send_message` has a `medium` floor, a local lane cannot label a proposed message as `low` to reduce review.

Risk floors do not approve side effects. They only prevent local lanes from understating risk.

## Exposure budgets

Exposure budgets adapt budget discipline to privacy and authority boundaries rather than provider spend.

Schema: `schemas/exposure-budget.schema.json`
Python helper: `sovereignty.ExposureBudget`

Budgets can enforce:

- maximum cloud exposure classification (`none`, `summary`, `excerpt`, or `raw`);
- maximum estimated exposed cloud tokens;
- maximum raw cloud tokens per run;
- maximum unmeasured packets per day;
- maximum side-effect proposals per packet;
- maximum local lane latency;
- whether privacy claims require measured exposure.

`unknown` exposure fails closed by default. A packet with `raw` exposure fails if the budget maximum is `summary`; telemetry with exposed-token estimates above the budget fails; and caller-attested exposure fails when measured exposure is required.

Example budget:

```json
{
  "schema_version": "0.1",
  "budget_id": "privacy-default",
  "max_cloud_exposure_classification": "summary",
  "max_exposed_tokens_estimated": 500,
  "max_raw_cloud_tokens_per_run": 0,
  "max_unmeasured_packets_per_day": 0,
  "max_side_effect_proposals_per_packet": 1,
  "max_local_latency_ms": 10000,
  "require_measured_for_privacy_claims": true
}
```

## Example policy

```json
{
  "schema_version": "0.1",
  "policy_id": "default-local-prep",
  "trusted_verifier_ids": ["sovereignty.recording_proxy.v0"],
  "max_cloud_exposure_classification": "summary",
  "require_measured_exposure_for_privacy_claims": true,
  "trusted_metadata_origins": ["authority", "verifier"],
  "forbidden_client_metadata_keys": [
    "policy_tags",
    "budget_tags",
    "authority_tags",
    "trust_tags"
  ],
  "forbidden_side_effect_types": ["deploy", "trade", "payment"],
  "risk_floor_by_effect_type": {
    "send_message": "medium",
    "deploy": "high"
  }
}
```

## Python usage

```python
from sovereignty import SovereigntyPolicy, validate_packet_dict

policy = SovereigntyPolicy.from_dict(policy_data)
packet = validate_packet_dict(packet_data)
policy.validate_packet(packet, metadata_origin="local_lane")
```

Validation returns the packet when allowed and raises `SovereigntyPolicyError` when the packet violates origin, exposure, or side-effect rules.
