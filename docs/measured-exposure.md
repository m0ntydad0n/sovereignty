# Measured exposure

Sovereignty separates two different claims:

- **caller-attested exposure**: the caller says what it sent to a cloud model;
- **measured exposure**: a verifier observed traffic crossing a configured boundary and produced evidence for the exposure claim.

Measured exposure is stronger than caller-attested exposure, but it is not magic. A verifier can only measure the traffic it is configured to see.

## First verifier shape

The first verifier should be a local recording boundary: a recording proxy, test harness, or adapter wrapper that sits between a local lane and any cloud model endpoint. It records request metadata and request-body digests, then emits a report. The report must avoid copying raw prompts, request bodies, API keys, hostnames, base URLs, local paths, or tokens.

The reference Python helper is `build_measured_exposure_report`. For an end-to-end adapter-wrapper prototype, use `RecordingBoundary`: it observes method, URL, and request body before an injected transport callable runs, then emits the same measured exposure report shape.

```python
from sovereignty import RecordedRequest, build_measured_exposure_report

report = build_measured_exposure_report(
    local_input="private source material",
    observed_requests=[
        RecordedRequest(
            method="POST",
            url="https://cloud.example/v1/chat/completions",
            body=b"redacted bytes observed by the local recorder",
        )
    ],
)
```

Adapter-wrapper prototype:

```python
from sovereignty import RecordingBoundary

local_input = "private source material"


def transport(method: str, url: str, body: bytes):
    # Call requests/httpx/urllib here in a real adapter.
    return {"status": 200}


boundary = RecordingBoundary(local_input=local_input, transport=transport)
boundary.request("POST", "https://cloud.example/v1/chat/completions", b"prompt bytes")
report = boundary.report(drop_observed_bodies=True)
```

A runnable version lives at `examples/recording_boundary.py`.

## Verifier report shape

A verifier report is evidence that can be attached to an `Exposure` as its evidence payload or referenced from a review packet.

```json
{
  "schema_version": "0.1",
  "trust_model": "measured",
  "classification": "none | excerpt | raw | unknown",
  "verifier_id": "sovereignty.recording_proxy.v0",
  "observed_request_count": 1,
  "transmitted_byte_count": 123,
  "evidence": {
    "local_input_digest": "sha256:...",
    "request_digests": ["sha256:..."],
    "observed_methods": ["POST"],
    "observed_url_schemes": ["https"]
  },
  "limitations": [
    "raw request bodies are not included",
    "raw URLs, hostnames, base URLs, local paths, and tokens are not included in the report",
    "semantic equivalence is not proven",
    "unmatched nonempty requests are classified as unknown",
    "measurement only covers traffic routed through the configured verifier boundary"
  ]
}
```

## Classification rules

The initial reference classifier is intentionally conservative:

- `none`: no cloud-bound request body was observed.
- `raw`: the normalized local input appears exactly inside an observed request body.
- `excerpt`: a material substring of the local input appears inside an observed request body.
- `unknown`: nonempty traffic was observed, but the verifier cannot prove whether it was summary, paraphrase, unrelated content, or encrypted/encoded content.

The reference helper does not claim `summary` from bytes alone. A semantic verifier may add a stricter, separately documented `summary` proof later, but caller-attested summaries must not be marketed as measured proof.

## Trust boundary

Measured exposure assumes:

1. the verifier code ran on the local side of the boundary;
2. the local lane routed all relevant cloud-bound traffic through that verifier;
3. the verifier saw request bodies before transport encryption, or it wrapped the adapter before the HTTP client;
4. the report was produced before untrusted code could mutate the evidence.

`RecordingBoundary` satisfies only the adapter-wrapper version of this model: it observes calls made through its injected `transport` callable. It does not intercept direct socket calls, browser traffic, subprocesses, DNS, plugins, or any request path that bypasses the wrapper.

If any of these assumptions is false, the report should be treated as incomplete evidence, not proof.

## Non-goals

Measured exposure does not prove:

- that every process on the machine avoided cloud egress;
- that all DNS, socket, browser, or plugin traffic was captured;
- that a cloud provider did not infer private details from metadata;
- that a paraphrase is semantically equivalent to the local input;
- that no side effects occurred.

Side effects remain governed by review packets and authority gating. A measured exposure report can say what crossed a configured boundary; it does not grant authority to act.

## Privacy policy

Verifier reports should be safe to show to a main/cloud agent. They should include digests and aggregate counts, not raw sensitive content or infrastructure details. In particular, reports must redact or omit:

- API keys, tokens, passwords, bearer headers, cookies, and credentials;
- local paths and usernames;
- base URLs, hostnames, endpoints, and private network addresses;
- raw prompt, completion, and request bodies.
