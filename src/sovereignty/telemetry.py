from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from .policy import SovereigntyPolicyError

FORBIDDEN_TELEMETRY_KEY_RE = re.compile(
    r"(?i)^(messages|response|prompt|completion|stdout|stderr|raw[_-]?input|raw[_-]?output|request[_-]?body|response[_-]?body|api[_-]?key|token|secret|password|base[_-]?url|endpoint|path)$"
)

VALID_STATUS = {"success", "failure", "timeout", "policy_blocked"}
VALID_LOCAL_LANE_STATUS = {"success", "failure", "timeout", "not_run"}
VALID_GUARDRAIL_STATUS = {
    "success",
    "guardrail_intervened",
    "guardrail_failed_to_respond",
    "not_run",
}
VALID_EXPOSURE_STATUS = {"measured", "caller_attested", "not_applicable", "unknown"}
VALID_SIDE_EFFECT_STATUS = {
    "proposed_none",
    "proposed_pending_review",
    "reviewed",
    "blocked",
    "not_applicable",
}


def default_privacy() -> dict[str, bool]:
    return {
        "metadata_only": True,
        "raw_payload_logged": False,
        "local_output_logged": False,
    }


def build_error_digest(message: str) -> str:
    return "sha256:" + hashlib.sha256(message.encode("utf-8")).hexdigest()


@dataclass
class PacketTelemetry:
    run_id: str
    packet_id: str
    trace_id: str
    adapter: str
    lane: str
    action: str
    status: str
    status_fields: dict[str, Any]
    timing: dict[str, Any]
    token_accounting: dict[str, int]
    privacy: dict[str, bool] = field(default_factory=default_privacy)
    consumer_session_id: str | None = None
    cost_accounting: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        validate_packet_telemetry(self)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "packet_id": self.packet_id,
            "trace_id": self.trace_id,
            "adapter": self.adapter,
            "lane": self.lane,
            "action": self.action,
            "status": self.status,
            "status_fields": dict(self.status_fields),
            "timing": dict(self.timing),
            "token_accounting": dict(self.token_accounting),
            "privacy": dict(self.privacy),
        }
        if self.consumer_session_id is not None:
            data["consumer_session_id"] = self.consumer_session_id
        if self.cost_accounting is not None:
            data["cost_accounting"] = dict(self.cost_accounting)
        if self.error is not None:
            data["error"] = dict(self.error)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PacketTelemetry":
        _reject_forbidden_keys(data)
        return cls(
            schema_version=str(data.get("schema_version") or "0.1"),
            run_id=_required_string(data, "run_id"),
            packet_id=_required_string(data, "packet_id"),
            trace_id=_required_string(data, "trace_id"),
            consumer_session_id=_optional_string(data, "consumer_session_id"),
            adapter=_required_string(data, "adapter"),
            lane=_required_string(data, "lane"),
            action=_required_string(data, "action"),
            status=_required_string(data, "status"),
            status_fields=dict(_required_mapping(data, "status_fields")),
            timing=dict(_required_mapping(data, "timing")),
            token_accounting=dict(_required_mapping(data, "token_accounting")),
            privacy=dict(data.get("privacy") or default_privacy()),
            cost_accounting=_optional_dict(data, "cost_accounting"),
            error=_optional_dict(data, "error"),
        )


def validate_packet_telemetry(telemetry: PacketTelemetry) -> PacketTelemetry:
    if telemetry.schema_version != "0.1":
        raise SovereigntyPolicyError("schema_version must be 0.1")
    for key in ["run_id", "packet_id", "trace_id", "adapter", "lane", "action"]:
        if not isinstance(getattr(telemetry, key), str) or not getattr(telemetry, key):
            raise SovereigntyPolicyError(f"{key} is required")
    if telemetry.status not in VALID_STATUS:
        raise SovereigntyPolicyError("status is invalid")

    _validate_status_fields(telemetry.status_fields)
    _validate_timing(telemetry.timing)
    _validate_token_accounting(telemetry.token_accounting)
    _validate_privacy(telemetry.privacy)
    if telemetry.consumer_session_id is not None and not telemetry.consumer_session_id:
        raise SovereigntyPolicyError("consumer_session_id must be nonempty when present")
    if telemetry.cost_accounting is not None and not isinstance(telemetry.cost_accounting, dict):
        raise SovereigntyPolicyError("cost_accounting must be an object")
    if telemetry.error is not None:
        _validate_error(telemetry.error)
    _reject_forbidden_keys(telemetry.to_dict())
    return telemetry


def _validate_status_fields(value: Mapping[str, Any]) -> None:
    expected = {
        "local_lane_status": VALID_LOCAL_LANE_STATUS,
        "guardrail_status": VALID_GUARDRAIL_STATUS,
        "exposure_status": VALID_EXPOSURE_STATUS,
        "side_effect_status": VALID_SIDE_EFFECT_STATUS,
    }
    for key, allowed in expected.items():
        if value.get(key) not in allowed:
            raise SovereigntyPolicyError(f"{key} is invalid")
    extra = set(value) - set(expected)
    if extra:
        raise SovereigntyPolicyError(f"unexpected status_fields key: {sorted(extra)[0]}")


def _validate_timing(value: Mapping[str, Any]) -> None:
    for key in ["started_at", "ended_at", "duration_ms"]:
        if key not in value:
            raise SovereigntyPolicyError(f"{key} is required")
    if not isinstance(value["started_at"], str) or not value["started_at"]:
        raise SovereigntyPolicyError("started_at is required")
    if value["ended_at"] is not None and not isinstance(value["ended_at"], str):
        raise SovereigntyPolicyError("ended_at must be a string or null")
    if value["duration_ms"] is not None and (
        not isinstance(value["duration_ms"], (int, float)) or value["duration_ms"] < 0
    ):
        raise SovereigntyPolicyError("duration_ms must be nonnegative or null")
    extra = set(value) - {"started_at", "ended_at", "duration_ms"}
    if extra:
        raise SovereigntyPolicyError(f"unexpected timing key: {sorted(extra)[0]}")


def _validate_token_accounting(value: Mapping[str, Any]) -> None:
    for key in [
        "raw_input_tokens_estimated",
        "local_output_tokens_estimated",
        "exposed_to_cloud_tokens_estimated",
        "kept_local_tokens_estimated",
    ]:
        if not isinstance(value.get(key), int) or value[key] < 0:
            raise SovereigntyPolicyError(f"{key} must be a nonnegative integer")
    extra = set(value) - {
        "raw_input_tokens_estimated",
        "local_output_tokens_estimated",
        "exposed_to_cloud_tokens_estimated",
        "kept_local_tokens_estimated",
    }
    if extra:
        raise SovereigntyPolicyError(f"unexpected token_accounting key: {sorted(extra)[0]}")


def _validate_privacy(value: Mapping[str, Any]) -> None:
    required = default_privacy()
    for key, expected in required.items():
        if value.get(key) is not expected:
            raise SovereigntyPolicyError(f"privacy.{key} must be {expected}")
    extra = set(value) - set(required)
    if extra:
        raise SovereigntyPolicyError(f"unexpected privacy key: {sorted(extra)[0]}")


def _validate_error(value: Mapping[str, Any]) -> None:
    if not isinstance(value.get("error_class"), str) or not value["error_class"]:
        raise SovereigntyPolicyError("error_class is required")
    digest = value.get("error_message_digest")
    if digest is not None and not re.fullmatch(r"sha256:[0-9a-f]{64}", str(digest)):
        raise SovereigntyPolicyError("error_message_digest must be sha256:<64 hex>")
    extra = set(value) - {"error_class", "error_message_digest"}
    if extra:
        raise SovereigntyPolicyError(f"unexpected error key: {sorted(extra)[0]}")


def _reject_forbidden_keys(value: Any, path: str = "telemetry") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if FORBIDDEN_TELEMETRY_KEY_RE.search(str(key)):
                raise SovereigntyPolicyError(f"forbidden telemetry key at {path}.{key}: {key}")
            _reject_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_keys(child, f"{path}[{index}]")


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


def _optional_string(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise SovereigntyPolicyError(f"{key} must be a nonempty string")
    return value


def _optional_dict(data: Mapping[str, Any], key: str) -> dict[str, Any] | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise SovereigntyPolicyError(f"{key} must be an object")
    return dict(value)
