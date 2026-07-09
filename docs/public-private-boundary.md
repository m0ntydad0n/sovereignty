# Public/private boundary

Sovereignty has two different surfaces by design:

- **Public Sovereignty** is the protocol layer: protocol contracts, JSON Schemas, reference validators, docs, release artifacts, and small adapter examples for local-prep / cloud-authority workflows.
- **Private router-core** is an implementation layer: implementation details, live router experiments, eval fixtures, private telemetry, backend health data, operational provider choices, and local command-center wiring.

The extraction rule is simple: publish stable contracts, not private wiring.

## What belongs in public

Public artifacts should be useful to another agent stack without revealing how this specific host is wired:

- review packet contracts;
- measured exposure reports;
- side-effect proposal and authority-side review records;
- metadata-only packet telemetry;
- policy-origin validation and exposure budgets;
- guardrail events and lane health records;
- execution broker decision packet contracts;
- sanitized examples that show local lanes preparing evidence while an authority-bearing agent or human decides.

The public project should answer: "What must cross the boundary, what must not cross it, and how can another runtime validate the packet?"

## What stays private

Private router-core may use Sovereignty contracts, but its live wiring is not the protocol. Do not publish:

- local endpoints;
- provider base URLs;
- host paths;
- API keys;
- tokens;
- private telemetry;
- raw prompts;
- request or response bodies;
- worker stdout/stderr;
- model downloads or local runtime paths;
- live operational lane maps;
- provider account details;
- dashboard state that reveals private workloads.

The public repo may use sanitized labels such as `local-extractor`, `direct:example:small-json`, or `openrouter:example/cheap-json`. It should not publish machine-specific endpoints, account-specific provider configuration, or raw task content.

## Broker boundary

An execution broker can choose between already-eligible backend candidates, but it is not the top-level router and it is not the authority layer.

The trust/router layer owns:

- lane selection;
- privacy classification;
- exposure policy;
- authority level;
- validator requirements;
- side-effect review;
- human approval and promotion gates.

The broker owns metadata-only backend choice after those gates:

- candidate backend ID;
- transport class such as `direct_provider`, `openrouter`, `ollama`, or `llama_cpp`;
- privacy and authority class;
- health state;
- p95 latency budget;
- cost ceiling;
- rejection reason codes;
- selected backend ID when one is eligible.

Broker decisions should remain metadata-only and shadow-safe by default. A broker decision packet records what would be selected; it does not prove a model call happened and it does not grant permission to execute side effects.

## Release discipline

Public releases should prefer boring evidence over mythology:

1. Add a contract test first.
2. Add the schema, doc, or reference helper.
3. Verify no raw operational data crosses the boundary.
4. Run the full suite.
5. Publish docs and schemas only after the private/private-derived details are sanitized.

Sovereignty does not guarantee privacy by existing. It gives local-first systems a contract for saying what crossed the boundary, what stayed local, and which authority-bearing actor is allowed to act.
