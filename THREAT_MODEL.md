# Threat Model

Version: 0.1-draft

## What Sovereignty tries to protect

Sovereignty helps agent builders separate private local prep work from authority-bearing actions.

It is designed to reduce these risks:

- raw private context being sent to cloud models by default;
- local models making final decisions or taking side effects without review;
- model metadata leaking API keys, host-local base URLs, or private paths;
- ambiguous claims about whether cloud exposure was actually avoided;
- unstructured local outputs being treated as trusted final answers.

## What Sovereignty does not protect

Sovereignty does not, by itself:

- sandbox arbitrary local model runtimes;
- prove local model output is truthful;
- prevent malware or prompt injection in host tools;
- guarantee secrets are absent from the raw input;
- authorize financial, legal, medical, trading, deployment, or client-facing actions;
- replace human review for sensitive workflows.

## Trust boundaries

Local lane:
- May read local input supplied to it.
- May produce a review packet.
- Must not invoke side-effecting tools.

Main agent:
- May review packets.
- May request more context.
- May invoke side effects only under the caller's tool policy.

Exposure telemetry:
- `caller_attested` means the caller asserts exposure; it is not proof.
- `measured` means a verifier observed egress or lack of egress.

## High-risk domains

For financial, legal, medical, trading, deployment, payment, client delivery, account management, or public publishing workflows, Sovereignty packets should be treated as scout output only. Human/main-agent review remains mandatory.
