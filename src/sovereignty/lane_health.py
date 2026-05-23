from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .policy import SovereigntyPolicyError

LANE_STATUSES = {"healthy", "degraded", "cooldown", "unavailable"}


@dataclass
class LaneHealth:
    lane: str
    status: str
    checked_at: str
    latency_ms: float | None = None
    last_success_at: str | None = None
    last_failure_class: str | None = None
    cooldown_until: str | None = None
    concurrency_limit: int | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        validate_lane_health(self)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "lane": self.lane,
            "status": self.status,
            "checked_at": self.checked_at,
        }
        for key in [
            "latency_ms",
            "last_success_at",
            "last_failure_class",
            "cooldown_until",
            "concurrency_limit",
        ]:
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LaneHealth":
        return cls(
            schema_version=str(data.get("schema_version") or "0.1"),
            lane=_required_string(data, "lane"),
            status=_required_string(data, "status"),
            checked_at=_required_string(data, "checked_at"),
            latency_ms=data.get("latency_ms"),
            last_success_at=data.get("last_success_at"),
            last_failure_class=data.get("last_failure_class"),
            cooldown_until=data.get("cooldown_until"),
            concurrency_limit=data.get("concurrency_limit"),
        )


def validate_lane_health(record: LaneHealth) -> LaneHealth:
    if record.schema_version != "0.1":
        raise SovereigntyPolicyError("schema_version must be 0.1")
    if not record.lane:
        raise SovereigntyPolicyError("lane is required")
    if record.status not in LANE_STATUSES:
        raise SovereigntyPolicyError("status is invalid")
    if not record.checked_at:
        raise SovereigntyPolicyError("checked_at is required")
    if record.latency_ms is not None and record.latency_ms < 0:
        raise SovereigntyPolicyError("latency_ms must be nonnegative")
    if record.concurrency_limit is not None and record.concurrency_limit < 1:
        raise SovereigntyPolicyError("concurrency_limit must be positive")
    return record


def _required_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise SovereigntyPolicyError(f"{key} is required")
    return value
