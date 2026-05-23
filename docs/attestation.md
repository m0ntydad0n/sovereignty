# Packet attestation boundary

This document is a design note, not a runtime implementation.

Sovereignty can later support JWS or JWT-style attestations for packet and policy digests. The goal is to let an authority-bearing tool know that a review packet or side-effect proposal passed through a known validator and policy boundary.

## What gets signed

Attestation should sign digests and metadata, not raw packets.

Fields:

- `issuer`: validator or verifier identity.
- `audience`: intended authority tool or reviewer.
- `packet_digest`: digest of the canonical review packet.
- `policy_digest`: digest of the policy that validated the packet.
- `expires_at`: short TTL expiration timestamp.
- `key_id`: signing key identifier.
- `jwks_url`: public key discovery URL for verification.

The design intentionally signs only canonical digests and metadata. It avoids embedding packet payloads so verifiers can confirm packet identity without spreading raw local outputs, proposed payloads, or private context through another artifact.

## What this proves

A valid attestation can prove:

- a known issuer signed a specific `packet_digest`;
- the issuer claimed a specific `policy_digest` was applied;
- the attestation was intended for a specific audience;
- the attestation was within its `expires_at` TTL when checked;
- the `key_id` maps to a public key from `jwks_url`.

## What this does not prove

A valid attestation does not prove:

- the local model output is correct;
- the side effect is safe to execute;
- the human or main agent approved the action;
- the raw local context was fully measured unless a measured-exposure verifier separately proves that boundary;
- semantic equivalence between raw context and summary;
- absence of malicious local-lane behavior before validation.

## Key rotation and TTL

Signing keys should rotate. Attestations should be short-lived. Authority tools should reject expired attestations and cache JWKS keys only according to a conservative TTL.

`key_id` lets verifiers select the active public key. `jwks_url` should be controlled by the issuer and served over authenticated transport.

## Threats

- replay: a valid old attestation could be reused against a new decision unless `expires_at`, `audience`, and packet identifiers are checked.
- stolen signing key: an attacker with the signing key can forge attestations until rotation and revocation.
- bypassing verifier: an authority tool might accept unsigned packets or fail open when verification fails.
- forged local packet: signing only proves validator passage; it does not prove the local packet was honestly generated.

## Relationship to side-effect review records

Attestation can attach to side-effect review records as digest metadata. A side-effect review record can reference the attested `packet_digest` and `policy_digest`, while still keeping approval/denial/execution metadata separate from the local-lane proposal.

Authority-bearing tools should still make their own policy decision. Attestation is evidence, not authorization.
