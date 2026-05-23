# Side-effect review records

A side-effect proposal is local-lane output. A side-effect review record is authority-side audit metadata.

Sovereignty keeps these objects separate so local prep lanes can propose actions without gaining approval or execution authority.

## Boundary

Local lanes may emit `schemas/side-effect-proposal.schema.json` objects inside a review packet. Those proposals are review-only.

A main agent, human, or policy reviewer may later emit a `schemas/side-effect-review-record.schema.json` object documenting the review decision and high-level execution status.

The review record does not contain raw payloads or raw execution results. It can include digests and references only.

## Required fields

- `schema_version`: currently `0.1`.
- `review_id`: stable review identifier.
- `packet_id`: review packet identifier.
- `effect_id`: side-effect proposal identifier.
- `review_decision`: one of `approved`, `denied`, `modified`, or `needs_human`.
- `reviewer_type`: one of `main_agent`, `human`, or `policy`.
- `reviewed_at`: review timestamp.
- `execution_status`: one of `not_executed`, `executed`, or `failed`.

Optional fields:

- `authority_tool`: authority-bearing tool that handled the action.
- `modified_payload_digest`: digest of a modified payload, if any.
- `result_digest`: digest of the result, if any.
- `result_ref`: external audit/reference handle.
- `notes_digest`: digest of reviewer notes.

## Forbidden fields

A side-effect review record must not include raw or authority-confusing fields such as:

- `result`
- `execution_result`
- `payload`
- `approved_by`
- `executed_at`

Raw payloads and results should stay in the authority-bearing system's own audit layer, not in Sovereignty local-prep protocol objects.

## Example

```json
{
  "schema_version": "0.1",
  "review_id": "rev_1",
  "packet_id": "pkt_1",
  "effect_id": "effect_1",
  "review_decision": "approved",
  "reviewer_type": "main_agent",
  "reviewed_at": "2026-05-23T12:00:00Z",
  "execution_status": "not_executed",
  "authority_tool": "github_issue_create",
  "notes_digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
}
```

This records an authority-side decision without giving the local lane execution state or raw result storage.
