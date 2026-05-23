# Operational records

Sovereignty defines optional metadata-only operational records for local-prep / cloud-authority systems. These records improve observability without turning the project into a gateway or logging raw payloads.

## Guardrail events

Guardrail events describe whether a guardrail ran at one stage of the flow:

- `pre_local`
- `post_local`
- `pre_authority`
- `post_authority`

Statuses are:

- `passed`
- `intervened`
- `failed_to_respond`
- `not_run`

A guardrail event can include a guardrail name, masked entity counts, and an intervention type (`none`, `blocked`, `modified`, or `escalated`).

It must not include raw blocked text, prompts, responses, request bodies, or response bodies.

Schema: `schemas/guardrail-event.schema.json`
Python helper: `sovereignty.GuardrailEvent`

## Lane health

Lane health records summarize local runtime availability and routing safety for a local lane.

Statuses are:

- `healthy`
- `degraded`
- `cooldown`
- `unavailable`

Optional metadata can include latency, last success time, last failure class, cooldown time, and concurrency limit.

Lane health is advisory metadata for policy and orchestration. It does not grant side-effect authority.

Schema: `schemas/lane-health.schema.json`
Python helper: `sovereignty.LaneHealth`

## Example guardrail event

```json
{
  "schema_version": "0.1",
  "event_id": "gr_1",
  "policy_id": "default-local-prep",
  "stage": "pre_authority",
  "status": "passed",
  "started_at": "2026-05-23T12:00:00Z",
  "ended_at": "2026-05-23T12:00:01Z",
  "duration_ms": 1000,
  "guardrail_name": "metadata-only-check",
  "masked_entity_counts": {"email": 2},
  "intervention_type": "none"
}
```

## Example lane health

```json
{
  "schema_version": "0.1",
  "lane": "hermes.local_router.coder",
  "status": "healthy",
  "checked_at": "2026-05-23T12:00:00Z",
  "latency_ms": 123,
  "last_success_at": "2026-05-23T11:59:59Z",
  "concurrency_limit": 2
}
```
