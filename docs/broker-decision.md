# Broker decision packets

A broker decision packet is a metadata-only record of how an execution broker ranked backend candidates after the trust/router layer has already chosen lane, privacy posture, authority level, validator requirement, and exposure policy.

The broker is not the router. It is not a gateway. It is not an authority-bearing actor.

## Scope

The broker may compare already-eligible backend paths by:

- backend ID;
- transport class (`direct_provider`, `openrouter`, `ollama`, `llama_cpp`, `local`, or `other`);
- health;
- p95 latency budget;
- cost ceiling;
- sync versus async capacity;
- rejection reason codes.

The broker must not store raw prompts, messages, completions, request bodies, response bodies, worker output, endpoints, provider base URLs, local paths, API keys, tokens, passwords, or credentials.

## Gate ordering

Broker candidates should show which gates were applied. Price scoring should happen only after earlier safety gates pass:

1. `validator_gate`
2. `privacy_gate`
3. `authority_gate`
4. `health_gate`
5. `p95_gate`
6. `price_scored`

For async fallback, queued candidates can use `async_queue_scored`, but privacy, authority, and health gates still apply. A cheap hosted backend does not override privacy or authority failure.

## Sync p95 budget

Synchronous decisions require an explicit `p95_ms` budget. A p50-only budget is not enough for sync UX or safety planning. If p95 is unknown, the decision should fail closed or choose an explicit async/shadow-only path.

## Execution and authority

`executed` must be `false` in the public broker-decision contract. The packet records a recommendation or shadow decision. It does not perform a model call, mutate router configuration, send messages, create issues, deploy, trade, pay, order, or approve side effects.

Side effects remain separate review-only proposals until an authority-bearing agent or human acts under policy.

## Schema

Language-agnostic validators can use:

- `schemas/broker-decision.schema.json`

Public example fixtures live in `examples/contracts/`:

- `broker-decision-privacy-reject.json`
- `broker-decision-trust-reject.json`
- `broker-decision-price-selected.json`
- `broker-decision-fallback-selected.json`

The schema intentionally uses sanitized backend labels. For example, `openrouter:example/cheap-json` may identify a transport class and model family without publishing private account configuration, local endpoints, or provider URLs.

The reference CLI can validate broker decision packets without executing anything:

```bash
sovereignty validate --schema broker-decision examples/contracts/broker-decision-price-selected.json
```
