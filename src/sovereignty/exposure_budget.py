from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .policy import SovereigntyPolicyError

EXPOSURE_ORDER = {"none": 0, "summary": 1, "excerpt": 2, "raw": 3}


@dataclass
class ExposureBudget:
    budget_id: str
    max_cloud_exposure_classification: str
    max_exposed_tokens_estimated: int | None = None
    max_raw_cloud_tokens_per_run: int | None = None
    max_unmeasured_packets_per_day: int | None = None
    max_side_effect_proposals_per_packet: int | None = None
    max_local_latency_ms: float | None = None
    require_measured_for_privacy_claims: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if self.schema_version != "0.1":
            raise SovereigntyPolicyError("schema_version must be 0.1")
        if not self.budget_id:
            raise SovereigntyPolicyError("budget_id is required")
        if self.max_cloud_exposure_classification not in EXPOSURE_ORDER:
            raise SovereigntyPolicyError("max_cloud_exposure_classification is invalid")
        for key in [
            "max_exposed_tokens_estimated",
            "max_raw_cloud_tokens_per_run",
            "max_unmeasured_packets_per_day",
            "max_side_effect_proposals_per_packet",
            "max_local_latency_ms",
        ]:
            value = getattr(self, key)
            if value is not None and value < 0:
                raise SovereigntyPolicyError(f"{key} must be nonnegative")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExposureBudget":
        return cls(
            schema_version=str(data.get("schema_version") or "0.1"),
            budget_id=_required_string(data, "budget_id"),
            max_cloud_exposure_classification=_required_string(
                data, "max_cloud_exposure_classification"
            ),
            max_exposed_tokens_estimated=data.get("max_exposed_tokens_estimated"),
            max_raw_cloud_tokens_per_run=data.get("max_raw_cloud_tokens_per_run"),
            max_unmeasured_packets_per_day=data.get("max_unmeasured_packets_per_day"),
            max_side_effect_proposals_per_packet=data.get(
                "max_side_effect_proposals_per_packet"
            ),
            max_local_latency_ms=data.get("max_local_latency_ms"),
            require_measured_for_privacy_claims=bool(
                data.get("require_measured_for_privacy_claims", False)
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "budget_id": self.budget_id,
            "max_cloud_exposure_classification": self.max_cloud_exposure_classification,
        }
        for key in [
            "max_exposed_tokens_estimated",
            "max_raw_cloud_tokens_per_run",
            "max_unmeasured_packets_per_day",
            "max_side_effect_proposals_per_packet",
            "max_local_latency_ms",
        ]:
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        data["require_measured_for_privacy_claims"] = self.require_measured_for_privacy_claims
        return data

    def validate_packet(self, packet: Any) -> Any:
        exposure = getattr(packet, "exposure", None)
        if exposure is None:
            raise SovereigntyPolicyError("packet exposure is required")
        classification = getattr(exposure, "classification", "unknown")
        if classification == "unknown":
            raise SovereigntyPolicyError("unknown exposure fails closed under budget")
        if classification not in EXPOSURE_ORDER:
            raise SovereigntyPolicyError(f"unsupported exposure classification: {classification}")
        if EXPOSURE_ORDER[classification] > EXPOSURE_ORDER[self.max_cloud_exposure_classification]:
            raise SovereigntyPolicyError(
                f"{classification} exposure exceeds budget maximum {self.max_cloud_exposure_classification}"
            )
        if self.require_measured_for_privacy_claims and getattr(exposure, "trust_model", None) != "measured":
            raise SovereigntyPolicyError("measured exposure is required by budget")
        side_effects = getattr(packet, "side_effects", []) or []
        if (
            self.max_side_effect_proposals_per_packet is not None
            and len(side_effects) > self.max_side_effect_proposals_per_packet
        ):
            raise SovereigntyPolicyError("too many side-effect proposals for budget")
        return packet

    def validate_telemetry(self, telemetry: Any) -> Any:
        token_accounting = getattr(telemetry, "token_accounting", {}) or {}
        exposed_tokens = int(token_accounting.get("exposed_to_cloud_tokens_estimated", 0))
        if (
            self.max_exposed_tokens_estimated is not None
            and exposed_tokens > self.max_exposed_tokens_estimated
        ):
            raise SovereigntyPolicyError("exposed tokens exceed budget")
        raw_tokens = int(token_accounting.get("raw_input_tokens_estimated", 0))
        if self.max_raw_cloud_tokens_per_run == 0:
            # Raw cloud tokens are represented by packet exposure; token telemetry alone
            # cannot prove raw exposure, so only enforce explicit raw-token allowance when nonzero.
            pass
        elif (
            self.max_raw_cloud_tokens_per_run is not None
            and raw_tokens > self.max_raw_cloud_tokens_per_run
        ):
            raise SovereigntyPolicyError("raw cloud tokens exceed budget")
        timing = getattr(telemetry, "timing", {}) or {}
        duration = timing.get("duration_ms")
        if (
            self.max_local_latency_ms is not None
            and duration is not None
            and duration > self.max_local_latency_ms
        ):
            raise SovereigntyPolicyError("local latency exceeds budget")
        return telemetry


def _required_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise SovereigntyPolicyError(f"{key} is required")
    return value
