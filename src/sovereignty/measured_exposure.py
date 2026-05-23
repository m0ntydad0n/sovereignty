from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlparse


DEFAULT_VERIFIER_ID = "sovereignty.recording_proxy.v0"
_MIN_EXCERPT_CHARS = 12


@dataclass(frozen=True)
class RecordedRequest:
    """A sanitized cloud-bound request observed by a local verifier.

    The body is used only to compute evidence and exposure classification. It is
    never copied into the report returned by build_measured_exposure_report.
    """

    method: str
    url: str
    body: bytes = b""


class RecordingBoundary:
    """Minimal adapter wrapper for measured exposure prototypes.

    The boundary records method, URL, and request body before forwarding the
    request to an injected transport callable. Reports omit raw bodies and URLs;
    callers can also drop retained raw bodies after reporting.
    """

    def __init__(
        self,
        *,
        local_input: str,
        transport: Callable[[str, str, bytes], Any],
        verifier_id: str = DEFAULT_VERIFIER_ID,
    ) -> None:
        self.local_input = local_input
        self.transport = transport
        self.verifier_id = verifier_id
        self.observed_requests: list[RecordedRequest] = []

    def request(self, method: str, url: str, body: bytes | str = b"") -> Any:
        body_bytes = body.encode("utf-8") if isinstance(body, str) else body
        observed = RecordedRequest(method=method, url=url, body=body_bytes)
        self.observed_requests.append(observed)
        return self.transport(method, url, body_bytes)

    def report(self, *, drop_observed_bodies: bool = False) -> dict[str, Any]:
        report = build_measured_exposure_report(
            local_input=self.local_input,
            observed_requests=self.observed_requests,
            verifier_id=self.verifier_id,
        )
        if drop_observed_bodies:
            self.observed_requests = [
                RecordedRequest(method=request.method, url=request.url, body=b"")
                for request in self.observed_requests
            ]
        return report


class _ClassificationRank:
    order = {"none": 0, "unknown": 1, "summary": 2, "excerpt": 3, "raw": 4}

    @classmethod
    def max(cls, values: Iterable[str]) -> str:
        return max(values, key=lambda value: cls.order[value], default="none")


def build_measured_exposure_report(
    *,
    local_input: str,
    observed_requests: list[RecordedRequest],
    verifier_id: str = DEFAULT_VERIFIER_ID,
    schema_version: str = "0.1",
) -> dict[str, Any]:
    """Build a measured exposure report from observed cloud-bound requests.

    The report intentionally stores digests and aggregate counts, not raw URLs,
    request bodies, base URLs, local paths, or tokens. It can prove that a local
    recorder observed bytes crossing a configured boundary; it cannot prove that
    every possible egress path was captured or that a paraphrase is semantically
    equivalent to the local input.
    """

    classifications = [
        _classify_request_body(local_input=local_input, body=request.body)
        for request in observed_requests
    ]
    classification = _ClassificationRank.max(classifications)
    transmitted_byte_count = sum(len(request.body) for request in observed_requests)

    return {
        "schema_version": schema_version,
        "trust_model": "measured",
        "classification": classification,
        "verifier_id": verifier_id,
        "observed_request_count": len(observed_requests),
        "transmitted_byte_count": transmitted_byte_count,
        "evidence": {
            "local_input_digest": _digest(local_input.encode("utf-8")),
            "request_digests": [_request_digest(request) for request in observed_requests],
            "observed_methods": sorted({request.method.upper() for request in observed_requests}),
            "observed_url_schemes": sorted(
                {_url_scheme(request.url) for request in observed_requests if _url_scheme(request.url)}
            ),
        },
        "limitations": [
            "raw request bodies are not included",
            "raw URLs, hostnames, base URLs, local paths, and tokens are not included in the report",
            "semantic equivalence is not proven",
            "unmatched nonempty requests are classified as unknown",
            "measurement only covers traffic routed through the configured verifier boundary",
        ],
    }


def _classify_request_body(*, local_input: str, body: bytes) -> str:
    if not body:
        return "none"

    body_text = body.decode("utf-8", errors="ignore")
    if not body_text.strip():
        return "none"

    normalized_input = _normalize(local_input)
    normalized_body = _normalize(body_text)
    if normalized_input and normalized_input in normalized_body:
        return "raw"

    if _longest_common_substring_length(normalized_input, normalized_body) >= _MIN_EXCERPT_CHARS:
        return "excerpt"

    return "unknown"


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _request_digest(request: RecordedRequest) -> str:
    method = request.method.upper().encode("utf-8")
    body_digest = hashlib.sha256(method + b"\0" + request.body).hexdigest()
    return "sha256:" + body_digest


def _url_scheme(url: str) -> str:
    return urlparse(url).scheme


def _longest_common_substring_length(left: str, right: str) -> int:
    if not left or not right:
        return 0

    previous = [0] * (len(right) + 1)
    best = 0
    for left_index in range(1, len(left) + 1):
        current = [0] * (len(right) + 1)
        for right_index in range(1, len(right) + 1):
            if left[left_index - 1] == right[right_index - 1]:
                current[right_index] = previous[right_index - 1] + 1
                best = max(best, current[right_index])
        previous = current
    return best
