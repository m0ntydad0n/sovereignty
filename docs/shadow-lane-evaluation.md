# Shadow-lane evaluation boundary

This document is a design note for future evaluation lanes. It is not a runtime implementation and does not put Sovereignty in the request path as a gateway.

A shadow lane is evaluation-only. It can observe metadata from a local-prep or authority-review flow and compute offline quality and latency signals. It must never affect final answer or side effects.

## Boundary

Shadow lanes may:

- compare candidate local lanes for quality and latency;
- classify packet outcomes with a classifier that only consumes metadata and approved summaries;
- evaluate a writer lane against policy and review outcomes;
- evaluate an extractor lane against schema validity, omission rates, and measured exposure reports;
- emit packet telemetry for aggregate evaluation;
- update lane health records for operational visibility.

Shadow lanes must not:

- execute side effects;
- approve, deny, or modify authority-bearing actions;
- change the final answer shown to a user;
- update production memory, policy, or routing state without separate review;
- train silently on raw private content;
- persist prompts, completions, stdout/stderr, request bodies, response bodies, local URLs, private paths, tokens, or credentials.

## Metadata-only inputs

Shadow-lane evaluation should use metadata-only artifacts:

- packet identifiers and digests;
- policy digests and verifier IDs;
- exposure classifications and token counts;
- schema validation status;
- guardrail event categories;
- side-effect proposal counts and risk classes;
- packet telemetry status and latency buckets;
- lane health status and cooldown metadata.

Raw local context remains outside the shadow lane. If a metric cannot be computed without raw private content, the metric should be marked unmeasured rather than weakening the privacy boundary.

## Metrics

Recommended metrics:

- quality: schema validity, policy pass rate, verifier agreement, review outcome agreement, and documented omission rates;
- latency: local preparation time, authority review time, verifier time, and end-to-end metadata timing;
- safety: guardrail intervention rate, blocked side-effect proposal rate, and unknown exposure rate;
- reliability: lane health transitions, cooldown frequency, error digest frequency, and retry counts.

## Classifier, writer, and extractor lanes

A classifier lane can score categories or risk classes from metadata and approved summaries. It must not grant authority tags or budget tags.

A writer lane can draft candidate summaries for offline comparison. A shadow writer cannot replace the production answer or create side-effect records.

An extractor lane can compare structured extraction quality against schema contracts. A shadow extractor cannot write production memory or silently enrich profiles.

## Relationship to packet telemetry and lane health

Packet telemetry is the primary event stream for shadow-lane evaluation. Lane health is the operational summary used to decide whether a lane is healthy, degraded, in cooldown, or unavailable.

Both artifacts remain metadata-only. They provide evidence for later review and tuning, not authorization to execute actions.

## Fail-closed behavior

If exposure is unknown or unmeasured and a budget exists, evaluation should fail closed for claims that depend on that measurement. Shadow evaluation can report `unmeasured`, but it should not infer safety from missing data.
