from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


class SovereigntyPolicyError(ValueError):
    """Raised when a Sovereignty packet or policy contract is invalid."""


EXPOSURE_ORDER = {"none": 0, "summary": 1, "excerpt": 2, "raw": 3}
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}
METADATA_ORIGINS = {"caller", "local_lane", "authority", "verifier"}
DEFAULT_FORBIDDEN_CLIENT_METADATA_KEYS = (
    "policy_tags",
    "budget_tags",
    "authority_tags",
    "trust_tags",
)


@dataclass
class SovereigntyPolicy:
    policy_id: str
    trusted_verifier_ids: set[str]
    max_cloud_exposure_classification: str = "summary"
    require_measured_exposure_for_privacy_claims: bool = True
    trusted_metadata_origins: set[str] = field(default_factory=lambda: {"authority", "verifier"})
    forbidden_client_metadata_keys: tuple[str, ...] = DEFAULT_FORBIDDEN_CLIENT_METADATA_KEYS
    forbidden_side_effect_types: tuple[str, ...] = ()
    risk_floor_by_effect_type: dict[str, str] = field(default_factory=dict)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if self.schema_version != "0.1":
            raise SovereigntyPolicyError("schema_version must be 0.1")
        if not self.policy_id:
            raise SovereigntyPolicyError("policy_id is required")
        if self.max_cloud_exposure_classification not in EXPOSURE_ORDER:
            raise SovereigntyPolicyError("max_cloud_exposure_classification is invalid")
        invalid_origins = set(self.trusted_metadata_origins) - {"authority", "verifier"}
        if invalid_origins:
            raise SovereigntyPolicyError(f"trusted metadata origins cannot include {sorted(invalid_origins)[0]}")
        for effect_type, risk in self.risk_floor_by_effect_type.items():
            if not effect_type:
                raise SovereigntyPolicyError("risk floor effect type is required")
            if risk not in RISK_ORDER:
                raise SovereigntyPolicyError(f"risk floor for {effect_type} is invalid")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SovereigntyPolicy":
        return cls(
            schema_version=str(data.get("schema_version") or "0.1"),
            policy_id=_required_string(data, "policy_id"),
            trusted_verifier_ids=set(_string_list(data, "trusted_verifier_ids")),
            max_cloud_exposure_classification=str(
                data.get("max_cloud_exposure_classification") or "summary"
            ),
            require_measured_exposure_for_privacy_claims=bool(
                data.get("require_measured_exposure_for_privacy_claims", True)
            ),
            trusted_metadata_origins=set(_string_list(data, "trusted_metadata_origins")),
            forbidden_client_metadata_keys=tuple(
                _string_list(data, "forbidden_client_metadata_keys")
            ),
            forbidden_side_effect_types=tuple(_string_list(data, "forbidden_side_effect_types")),
            risk_floor_by_effect_type=dict(data.get("risk_floor_by_effect_type") or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "policy_id": self.policy_id,
            "trusted_verifier_ids": sorted(self.trusted_verifier_ids),
            "max_cloud_exposure_classification": self.max_cloud_exposure_classification,
            "require_measured_exposure_for_privacy_claims": self.require_measured_exposure_for_privacy_claims,
            "trusted_metadata_origins": sorted(self.trusted_metadata_origins),
            "forbidden_client_metadata_keys": list(self.forbidden_client_metadata_keys),
            "forbidden_side_effect_types": list(self.forbidden_side_effect_types),
            "risk_floor_by_effect_type": dict(self.risk_floor_by_effect_type),
        }

    def validate_packet(self, packet: Any, *, metadata_origin: str = "local_lane") -> Any:
        if metadata_origin not in METADATA_ORIGINS:
            raise SovereigntyPolicyError(f"unsupported metadata origin: {metadata_origin}")
        self._validate_metadata_origin(packet, metadata_origin)
        self._validate_exposure(packet)
        self._validate_side_effects(packet)
        return packet

    def _validate_metadata_origin(self, packet: Any, metadata_origin: str) -> None:
        if metadata_origin in self.trusted_metadata_origins:
            return
        metadata = getattr(packet, "model_metadata", {}) or {}
        for key in self.forbidden_client_metadata_keys:
            if _contains_key(metadata, key):
                raise SovereigntyPolicyError(
                    f"metadata key {key} cannot be supplied by {metadata_origin}"
                )

    def _validate_exposure(self, packet: Any) -> None:
        exposure = getattr(packet, "exposure", None)
        if exposure is None:
            raise SovereigntyPolicyError("packet exposure is required")
        classification = getattr(exposure, "classification", "unknown")
        if classification == "unknown":
            raise SovereigntyPolicyError("unknown exposure fails closed under policy")
        if classification not in EXPOSURE_ORDER:
            raise SovereigntyPolicyError(f"unsupported exposure classification: {classification}")
        if EXPOSURE_ORDER[classification] > EXPOSURE_ORDER[self.max_cloud_exposure_classification]:
            raise SovereigntyPolicyError(
                f"exposure classification {classification} exceeds policy maximum {self.max_cloud_exposure_classification}"
            )
        if getattr(exposure, "trust_model", None) == "measured":
            verifier_id = _extract_verifier_id(getattr(exposure, "evidence", None))
            if verifier_id not in self.trusted_verifier_ids:
                raise SovereigntyPolicyError(f"untrusted measured exposure verifier: {verifier_id}")
        elif self.require_measured_exposure_for_privacy_claims:
            raise SovereigntyPolicyError("measured exposure is required by policy")

    def _validate_side_effects(self, packet: Any) -> None:
        side_effects = getattr(packet, "side_effects", []) or []
        for effect in side_effects:
            effect_type = str(effect.get("effect_type", ""))
            if effect_type in self.forbidden_side_effect_types:
                raise SovereigntyPolicyError(f"side-effect type is forbidden by policy: {effect_type}")
            floor = self.risk_floor_by_effect_type.get(effect_type)
            risk = str(effect.get("risk", ""))
            if floor and RISK_ORDER.get(risk, -1) < RISK_ORDER[floor]:
                raise SovereigntyPolicyError(
                    f"side-effect risk floor for {effect_type} is {floor}; got {risk}"
                )


def _extract_verifier_id(evidence: Any) -> str | None:
    if isinstance(evidence, Mapping):
        verifier_id = evidence.get("verifier_id")
        return str(verifier_id) if verifier_id else None
    return None


def _contains_key(value: Any, key: str) -> bool:
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            if child_key == key or _contains_key(child_value, key):
                return True
    elif isinstance(value, list):
        return any(_contains_key(child, key) for child in value)
    return False


def _required_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise SovereigntyPolicyError(f"{key} is required")
    return value


def _string_list(data: Mapping[str, Any], key: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise SovereigntyPolicyError(f"{key} must be a list of nonempty strings")
    return list(value)
