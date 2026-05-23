# Packet telemetry

Sovereignty packet telemetry is a metadata-only operational record for a local-prep run and its review packet.

It is designed for observability without becoming gateway request/response logging. A local lane may inspect raw local context and produce a `ReviewPacket`; telemetry records only identifiers, status, timing, token estimates, privacy flags, and digest-only error metadata.

## Non-goals

Packet telemetry is not:

- a model gateway log;
- a prompt or completion archive;
- a substitute for measured exposure evidence;
- authority to approve or execute side effects.

## Required fields

The canonical schema is `schemas/packet-telemetry.schema.json`.

Required top-level fields:

- `schema_version`: currently `0.1`.
- `run_id`: local-prep run identifier.
- `packet_id`: review packet identifier.
- `trace_id`: correlation identifier for the local-prep / authority-review flow.
- `adapter`: adapter name, such as `hermes-local-router`.
- `lane`: local lane name.
- `action`: prep action, such as `code_triage`, `extract`, `classify`, or `draft`.
- `status`: one of `success`, `failure`, `timeout`, or `policy_blocked`.
- `status_fields`: structured statuses for lane, guardrail, exposure, and side-effect state.
- `timing`: start/end timestamps and duration.
- `token_accounting`: estimated local input/output and cloud-exposed token counts.
- `privacy`: hard privacy flags.

Optional fields:

- `consumer_session_id`: external session correlation ID if safe to expose.
- `cost_accounting`: non-secret aggregate cost metadata.
- `error`: digest-only error metadata.

## Privacy guarantees

Telemetry must remain metadata-only.

The schema and Python helper reject raw or sensitive field names including:

- `messages`
- `response`
- `prompt`
- `completion`
- `stdout`
- `stderr`
- `raw_input`
- `raw_output`
- `request_body`
- `response_body`
- `api_key`
- `token`
- `secret`
- `password`
- `base_url`
- `endpoint`
- `path`

Telemetry privacy flags are constants:

```json
{
  "metadata_only": true,
  "raw_payload_logged": false,
  "local_output_logged": false
}
```

If an integration needs to preserve debugging detail, it should store a digest or aggregate count, not raw payloads. Raw prompts, local model outputs, request/response bodies, stdout/stderr, credentials, local paths, host-local URLs, and local base URLs do not belong in telemetry.

## Difference from gateway request logging

Gateways commonly observe provider requests, responses, retries, costs, fallbacks, and bodies. Sovereignty is not a gateway. Its telemetry describes the local-prep handoff:

1. A local lane ran.
2. It produced a review packet.
3. A measured or attested exposure state exists.
4. Any side effect remains proposed, pending review, reviewed, blocked, or not applicable.
5. The main agent or human remains the authority for final answers and actions.

Telemetry may be useful beside a gateway, but it should not copy gateway request/response logs into Sovereignty protocol objects.

## Error handling

Failures should record only error class and an optional digest:

```json
{
  "error_class": "TimeoutError",
  "error_message_digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

Use `sovereignty.build_error_digest(message)` to hash raw error text before attaching it. Do not include tracebacks, tool stdout/stderr, private paths, URLs, tokens, or provider payloads.

## Hermes local-router mapping

A Hermes local-router adapter can map one local worker call into telemetry as follows:

- `adapter`: `hermes-local-router`
- `lane`: the safe local lane, e.g. `hermes.local_router.coder`
- `action`: the local-router action, e.g. `code_triage`
- `packet_id`: the emitted `ReviewPacket.packet_id`
- `status_fields.local_lane_status`: local worker result status
- `status_fields.exposure_status`: `measured`, `caller_attested`, `not_applicable`, or `unknown`
- `status_fields.side_effect_status`: `proposed_pending_review` when the packet contains review-only side-effect proposals
- `token_accounting.exposed_to_cloud_tokens_estimated`: estimate of compact packet/review text exposed to the authority stage
- `token_accounting.kept_local_tokens_estimated`: estimate of raw context that stayed local

The runnable example at `examples/hermes/local_router_review_packet.py` emits both a review packet and packet telemetry.

## Success example

```json
{
  "schema_version": "0.1",
  "run_id": "run_1",
  "packet_id": "pkt_1",
  "trace_id": "trace_1",
  "adapter": "hermes-local-router",
  "lane": "hermes.local_router.coder",
  "action": "code_triage",
  "status": "success",
  "status_fields": {
    "local_lane_status": "success",
    "guardrail_status": "not_run",
    "exposure_status": "measured",
    "side_effect_status": "proposed_pending_review"
  },
  "timing": {
    "started_at": "2026-05-23T12:00:00Z",
    "ended_at": "2026-05-23T12:00:01Z",
    "duration_ms": 1000
  },
  "token_accounting": {
    "raw_input_tokens_estimated": 1200,
    "local_output_tokens_estimated": 120,
    "exposed_to_cloud_tokens_estimated": 180,
    "kept_local_tokens_estimated": 1020
  },
  "privacy": {
    "metadata_only": true,
    "raw_payload_logged": false,
    "local_output_logged": false
  }
}
```

## Failure example

```json
{
  "schema_version": "0.1",
  "run_id": "run_2",
  "packet_id": "pkt_2",
  "trace_id": "trace_2",
  "adapter": "hermes-local-router",
  "lane": "hermes.local_router.coder",
  "action": "code_triage",
  "status": "timeout",
  "status_fields": {
    "local_lane_status": "timeout",
    "guardrail_status": "not_run",
    "exposure_status": "unknown",
    "side_effect_status": "not_applicable"
  },
  "timing": {
    "started_at": "2026-05-23T12:00:00Z",
    "ended_at": null,
    "duration_ms": null
  },
  "token_accounting": {
    "raw_input_tokens_estimated": 1200,
    "local_output_tokens_estimated": 0,
    "exposed_to_cloud_tokens_estimated": 0,
    "kept_local_tokens_estimated": 1200
  },
  "privacy": {
    "metadata_only": true,
    "raw_payload_logged": false,
    "local_output_logged": false
  },
  "error": {
    "error_class": "TimeoutError",
    "error_message_digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }
}
```
