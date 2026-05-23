from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from .policy import SovereigntyPolicyError

REVIEW_DECISIONS = {"approved", "denied", "modified", "needs_human"}
REVIEWER_TYPES = {"main_agent", "human", "policy"}
EXECUTION_STATUSES = {"not_executed", "executed", "failed"}
DIGEST_FIELDS = {"modified_payload_digest", "result_digest", "notes_digest"}
FORBIDDEN_REVIEW_FIELDS = {
    "result",
    "execution_result",
    "payload",
    "approved_by",
    "executed_at",
}
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass
class SideEffectReviewRecord:
    review_id: str
    packet_id: str
    effect_id: str
    review_decision: str
    reviewer_type: str
    reviewed_at: str
    execution_status: str
    authority_tool: str | None = None
    modified_payload_digest: str | None = None
    result_digest: str | None = None
    result_ref: str | None = None
    notes_digest: str | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        validate_side_effect_review_record(self)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "review_id": self.review_id,
            "packet_id": self.packet_id,
            "effect_id": self.effect_id,
            "review_decision": self.review_decision,
            "reviewer_type": self.reviewer_type,
            "reviewed_at": self.reviewed_at,
            "execution_status": self.execution_status,
        }
        for key in [
            "authority_tool",
            "modified_payload_digest",
            "result_digest",
            "result_ref",
            "notes_digest",
        ]:
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SideEffectReviewRecord":
        _reject_forbidden_fields(data)
        allowed = {
            "schema_version",
            "review_id",
            "packet_id",
            "effect_id",
            "review_decision",
            "reviewer_type",
            "reviewed_at",
            "execution_status",
            "authority_tool",
            "modified_payload_digest",
            "result_digest",
            "result_ref",
            "notes_digest",
        }
        extra = set(data) - allowed
        if extra:
            raise SovereigntyPolicyError(f"unexpected review record field: {sorted(extra)[0]}")
        return cls(
            schema_version=str(data.get("schema_version") or "0.1"),
            review_id=_required_string(data, "review_id"),
            packet_id=_required_string(data, "packet_id"),
            effect_id=_required_string(data, "effect_id"),
            review_decision=_required_string(data, "review_decision"),
            reviewer_type=_required_string(data, "reviewer_type"),
            reviewed_at=_required_string(data, "reviewed_at"),
            execution_status=_required_string(data, "execution_status"),
            authority_tool=_optional_string(data, "authority_tool"),
            modified_payload_digest=_optional_string(data, "modified_payload_digest"),
            result_digest=_optional_string(data, "result_digest"),
            result_ref=_optional_string(data, "result_ref"),
            notes_digest=_optional_string(data, "notes_digest"),
        )


def validate_side_effect_review_record(
    record: SideEffectReviewRecord,
) -> SideEffectReviewRecord:
    if record.schema_version != "0.1":
        raise SovereigntyPolicyError("schema_version must be 0.1")
    for key in ["review_id", "packet_id", "effect_id", "reviewed_at"]:
        if not isinstance(getattr(record, key), str) or not getattr(record, key):
            raise SovereigntyPolicyError(f"{key} is required")
    if record.review_decision not in REVIEW_DECISIONS:
        raise SovereigntyPolicyError("review_decision is invalid")
    if record.reviewer_type not in REVIEWER_TYPES:
        raise SovereigntyPolicyError("reviewer_type is invalid")
    if record.execution_status not in EXECUTION_STATUSES:
        raise SovereigntyPolicyError("execution_status is invalid")
    for key in DIGEST_FIELDS:
        value = getattr(record, key)
        if value is not None and not DIGEST_RE.fullmatch(value):
            raise SovereigntyPolicyError(f"{key} must be sha256:<64 hex>")
    if record.authority_tool is not None and not record.authority_tool:
        raise SovereigntyPolicyError("authority_tool must be nonempty when present")
    if record.result_ref is not None and not record.result_ref:
        raise SovereigntyPolicyError("result_ref must be nonempty when present")
    return record


def _reject_forbidden_fields(data: Mapping[str, Any]) -> None:
    forbidden = FORBIDDEN_REVIEW_FIELDS.intersection(data)
    if forbidden:
        field = sorted(forbidden)[0]
        raise SovereigntyPolicyError(f"forbidden side-effect review field: {field}")


def _required_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise SovereigntyPolicyError(f"{key} is required")
    return value


def _optional_string(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise SovereigntyPolicyError(f"{key} must be a nonempty string")
    return value
