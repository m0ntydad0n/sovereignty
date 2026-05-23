# Protocol, not gateway

Sovereignty is a protocol, not a gateway.

That distinction matters because Sovereignty is adjacent to projects such as
LiteLLM, RouteLLM, Portkey, and other proxy/router stacks, but it is not trying
to win the same layer. Gateways generally sit on the transport path between an
application and one or more model providers. Sovereignty defines the review
contract between local preparation work and an authority-bearing agent or human.

The useful comparison is not better/worse. It is layer and responsibility.

## What gateways optimize

Gateway and router projects commonly focus on operational model access:

| Dimension | Typical gateway responsibility |
| --- | --- |
| Provider routing | Choose a model/provider for a request based on policy, latency, cost, availability, or quality. |
| Cost and fallback policy | Select cheaper models, fall back from failed providers, or split traffic across vendors. |
| Retries and rate limits | Retry transient failures, apply budgets, smooth traffic, and normalize provider errors. |
| Observability and billing | Track requests, tokens, latency, errors, spend, tenants, and provider-level usage. |
| API compatibility | Present a stable API while translating across provider-specific APIs. |

Those are useful infrastructure concerns. Sovereignty can use them, sit beside
them, or emit packets that eventually pass through them. It does not need to
replace that layer.

## What Sovereignty defines

Sovereignty focuses on agent control boundaries:

| Dimension | Sovereignty responsibility |
| --- | --- |
| Review packets | Local lanes return structured packets containing local output, redacted metadata, exposure claims, and proposed side effects. |
| Authority gating | Local lanes may prepare or propose. The main agent or human retains authority over final answers and side effects. |
| Exposure accounting | Packets distinguish what source context reached a cloud/main model and how that claim is known. |
| Side-effect proposals | Local lanes describe requested actions for review; they do not execute or mark those actions approved. |
| Policy validation | Callers can validate packet shape, metadata hygiene, exposure class, and review requirements before acting. |

This makes Sovereignty closer to a handoff contract than a model switchboard. A
local model can classify, extract, draft, triage, or check sensitivity against
private context. The output that leaves the local boundary is a review packet,
not an implicit grant of authority.

## Authority gating vs transport routing

Transport routing answers questions such as:

- Which provider should handle this model request?
- Should the request retry on another model if it fails?
- How should provider-specific APIs be normalized?
- How should token usage and latency be recorded?

Authority gating answers different questions:

- Is this local output sufficient for a main agent or human to review?
- Did the local lane propose a side effect rather than executing it?
- Does the packet require review before an authority-bearing tool acts?
- Is the target/payload of a proposed action visible before execution?

A gateway can route an LLM call safely and still be indifferent to whether an
agent should send an email, write a file, open an issue, deploy code, or trade an
asset. Sovereignty is specifically concerned with that authority boundary.

## Exposure accounting

Sovereignty does not rely on vague privacy claims. It requires exposure claims to
state both classification and trust model.

The exposure classification describes what kind of source context reached a
cloud/main model: raw input, excerpt, summary, none, or unknown.

The trust model describes how that claim is known:

- `caller_attested`: the caller says what it sent. This is useful for plumbing,
  but it is not proof of whole-system egress.
- `measured`: a configured verifier boundary observed the request path and
  produced evidence. This is evidence from that boundary only, not a claim about
  direct sockets, subprocesses, browsers, plugins, DNS, or every possible bypass.
- `not_applicable`: no exposure claim applies for that packet or context.

This is intentionally conservative. A measured report can be stronger than a
caller-attested claim, but it still has a boundary and limitations.

## Why side effects stay outside local lanes

Sovereignty assumes local lanes are useful for preparation, not authority. A
local lane may inspect local context and produce a proposed action, but execution
belongs to the main agent or human reviewer under its own tool policy.

That separation keeps reviewable state explicit:

- intent is visible before action;
- target and payload can be inspected;
- risk can be declared;
- approval/execution state is not forged by the proposer;
- the authority-bearing layer can deny, edit, log, or execute the action.

The side-effect proposal schema is therefore review-only. It excludes approval
and execution fields such as `approved_by`, `executed_at`, `execution_result`,
`result`, and `status`.

## Composing with gateways

Sovereignty can compose with gateways instead of replacing them.

Example architecture:

1. A local model runtime performs private extraction or triage.
2. Sovereignty validates the local lane's review packet.
3. An optional measured boundary records what leaves the local boundary.
4. The main agent reviews the packet and decides whether to answer or act.
5. If the main agent needs a cloud model, that model request may be routed
   through LiteLLM, RouteLLM, Portkey, or another gateway.
6. If a side effect is approved, the authority-bearing tool executes it and logs
   its own result outside the proposal.

In that setup, the gateway remains responsible for provider access and routing.
Sovereignty remains responsible for the local-prep / cloud-authority contract.

## Non-goals

Sovereignty does not claim to be:

- a provider gateway;
- a provider router;
- a sandbox;
- a whole-machine egress monitor;
- proof that a model is safe or correct;
- a substitute for human review in high-risk domains.

The project should make narrow claims that can be tested: packet validation,
metadata redaction, exposure trust labels, measured-boundary evidence, and
review-only side-effect proposals.
