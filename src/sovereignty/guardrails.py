from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .policy import SovereigntyPolicyError

GUARDRAIL_STAGES = {"pre_local", "post_local", "pre_authority", "post_authority"}
GUARDRAIL_STATUSES = {"passed", "intervened", "failed_to_respond", "not_run"}
INTERVENTION_TYPES = {"none", "blocked", "modified", "escalated"}
FORBIDDEN_GUARDRAIL_FIELDS = {"prompt", "response", "request_body", "response_body", "blocked_text"}


@dataclass
class GuardrailEvent:
    event_id: str
    policy_id: str
    stage: str
    status: str
    started_at: str
    ended_at: str | None
    duration_ms: float | None
    guardrail_name: str | None = None
    masked_entity_counts: dict[str, int] = field(default_factory=dict)
    intervention_type: str | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        validate_guardrail_event(self)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "policy_id": self.policy_id,
            "stage": self.stage,
            "status": self.status,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
        }
        if self.guardrail_name is not None:
            data["guardrail_name"] = self.guardrail_name
        if self.masked_entity_counts:
            data["masked_entity_counts"] = dict(self.masked_entity_counts)
        if self.intervention_type is not None:
            data["intervention_type"] = self.intervention_type
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GuardrailEvent":
        forbidden = FORBIDDEN_GUARDRAIL_FIELDS.intersection(data)
        if forbidden:
            raise SovereigntyPolicyError(f"forbidden guardrail event field: {sorted(forbidden)[0]}")
        return cls(
            schema_version=str(data.get("schema_version") or "0.1"),
            event_id=_required_string(data, "event_id"),
            policy_id=_required_string(data, "policy_id"),
            stage=_required_string(data, "stage"),
            status=_required_string(data, "status"),
            started_at=_required_string(data, "started_at"),
            ended_at=data.get("ended_at"),
            duration_ms=data.get("duration_ms"),
            guardrail_name=data.get("guardrail_name"),
            masked_entity_counts=dict(data.get("masked_entity_counts") or {}),
            intervention_type=data.get("intervention_type"),
        )


def validate_guardrail_event(event: GuardrailEvent) -> GuardrailEvent:
    if event.schema_version != "0.1":
        raise SovereigntyPolicyError("schema_version must be 0.1")
    for key in ["event_id", "policy_id", "started_at"]:
        if not getattr(event, key):
            raise SovereigntyPolicyError(f"{key} is required")
    if event.stage not in GUARDRAIL_STAGES:
        raise SovereigntyPolicyError("stage is invalid")
    if event.status not in GUARDRAIL_STATUSES:
        raise SovereigntyPolicyError("status is invalid")
    if event.duration_ms is not None and event.duration_ms < 0:
        raise SovereigntyPolicyError("duration_ms must be nonnegative or null")
    if event.intervention_type is not None and event.intervention_type not in INTERVENTION_TYPES:
        raise SovereigntyPolicyError("intervention_type is invalid")
    for key, value in event.masked_entity_counts.items():
        if not isinstance(key, str) or not isinstance(value, int) or value < 0:
            raise SovereigntyPolicyError("masked_entity_counts must be string to nonnegative int")
    return event


def _required_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise SovereigntyPolicyError(f"{key} is required")
    return value
