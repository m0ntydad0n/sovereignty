from __future__ import annotations

from dataclasses import dataclass

from .policy import SovereigntyPolicyError

EXPOSURE_CLASSIFICATIONS = {"raw", "excerpt", "summary", "none", "unknown"}
EXPOSURE_TRUST_MODELS = {"caller_attested", "measured", "not_applicable"}


@dataclass(frozen=True)
class Exposure:
    classification: str
    trust_model: str
    evidence: str | None = None

    def __post_init__(self) -> None:
        if self.classification not in EXPOSURE_CLASSIFICATIONS:
            raise SovereigntyPolicyError(
                f"unsupported exposure classification: {self.classification}"
            )
        if self.trust_model not in EXPOSURE_TRUST_MODELS:
            raise SovereigntyPolicyError(
                f"unsupported exposure trust_model: {self.trust_model}"
            )
        if self.trust_model == "measured" and not self.evidence:
            raise SovereigntyPolicyError("measured exposure requires evidence")
