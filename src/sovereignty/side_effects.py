from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .policy import SovereigntyPolicyError

SIDE_EFFECT_RISKS = {"low", "medium", "high"}
SIDE_EFFECT_REQUIRED_FIELDS = {
    "effect_id",
    "effect_type",
    "tool",
    "intent",
    "target",
    "payload",
    "risk",
}
SIDE_EFFECT_EXECUTION_FIELDS = {
    "executed_at",
    "execution_id",
    "execution_result",
    "result",
    "status",
    "approved_at",
    "approved_by",
}


@dataclass(frozen=True)
class SideEffectProposal:
    """A proposed side effect for main-agent or human review.

    This object is a proposal only. It must not contain execution receipts,
    approval state, or evidence that the local lane performed the action.
    """

    effect_id: str
    effect_type: str
    tool: str
    intent: str
    target: dict[str, Any]
    payload: dict[str, Any]
    risk: str

    def __post_init__(self) -> None:
        if self.risk not in SIDE_EFFECT_RISKS:
            raise SovereigntyPolicyError(f"unsupported side-effect risk: {self.risk}")
        _require_non_empty_string(self.effect_id, "effect_id")
        _require_non_empty_string(self.effect_type, "effect_type")
        _require_non_empty_string(self.tool, "tool")
        _require_non_empty_string(self.intent, "intent")
        if not isinstance(self.target, dict):
            raise SovereigntyPolicyError("target must be an object")
        if not isinstance(self.payload, dict):
            raise SovereigntyPolicyError("payload must be an object")

    def to_dict(self) -> dict[str, Any]:
        return {
            "effect_id": self.effect_id,
            "effect_type": self.effect_type,
            "tool": self.tool,
            "intent": self.intent,
            "target": self.target,
            "payload": self.payload,
            "risk": self.risk,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SideEffectProposal":
        unexpected_execution_fields = sorted(
            key for key in data if key in SIDE_EFFECT_EXECUTION_FIELDS
        )
        if unexpected_execution_fields:
            joined = ", ".join(unexpected_execution_fields)
            raise SovereigntyPolicyError(
                f"side-effect proposal must not contain execution state: {joined}"
            )

        missing = sorted(field for field in SIDE_EFFECT_REQUIRED_FIELDS if field not in data)
        if missing:
            raise SovereigntyPolicyError(
                f"side-effect proposal missing required fields: {', '.join(missing)}"
            )

        return cls(
            effect_id=_required_string(data, "effect_id"),
            effect_type=_required_string(data, "effect_type"),
            tool=_required_string(data, "tool"),
            intent=_required_string(data, "intent"),
            target=dict(_required_mapping(data, "target")),
            payload=dict(_required_mapping(data, "payload")),
            risk=_required_string(data, "risk"),
        )


def validate_side_effect_proposal(data: Mapping[str, Any]) -> SideEffectProposal:
    return SideEffectProposal.from_dict(data)


def validate_side_effect_proposals(values: list[Any]) -> list[dict[str, Any]]:
    validated = []
    for index, value in enumerate(values):
        if not isinstance(value, Mapping):
            raise SovereigntyPolicyError(f"side_effects[{index}] must be an object")
        try:
            validated.append(validate_side_effect_proposal(value).to_dict())
        except SovereigntyPolicyError as exc:
            raise SovereigntyPolicyError(f"side_effects[{index}]: {exc}") from exc
    return validated


def _required_mapping(data: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = data.get(key)
    if not isinstance(value, Mapping):
        raise SovereigntyPolicyError(f"{key} must be an object")
    return value


def _required_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise SovereigntyPolicyError(f"{key} is required")
    return value


def _require_non_empty_string(value: str, key: str) -> None:
    if not isinstance(value, str) or not value:
        raise SovereigntyPolicyError(f"{key} is required")
