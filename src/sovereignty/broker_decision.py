from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from .policy import SovereigntyPolicyError

FORBIDDEN_KEY_RE = re.compile(
    r"(messages|response|prompt|completion|stdout|stderr|raw[_-]?input|raw[_-]?output|"
    r"raw[_-]?prompt|worker[_-]?output|request[_-]?body|response[_-]?body|api[_-]?key|"
    r"token|secret|password|credential|base[_-]?url|endpoint|url|path|local[_-]?path|dsn|"
    r"connection[_-]?string)",
    re.IGNORECASE,
)

AUTHORITY_LEVEL_RE = re.compile(r"^A[0-6]$")
EXPOSURE_ORIGINS = {"precloud_compacted", "postcloud_hint", "local_only", "unknown"}
EXPOSURE_STATES = {"local_only_raw", "compact_cloud", "raw_cloud_allowed", "forbidden_cloud", "unknown"}
EXECUTION_MODES = {"sync", "async_queue", "shadow_only", "none"}
BUDGET_MODES = {"sync", "async", "shadow_only"}
TRANSPORTS = {"direct_provider", "openrouter", "ollama", "llama_cpp", "local", "other"}
PRIVACY_CLASSES = {"local_raw", "redacted_or_compact_cloud", "raw_cloud_allowed", "metadata_only", "unknown"}
AUTHORITY_CLASSES = {"proposal_only", "read_only", "no_side_effects", "unknown"}
STAGES = {
    "validator_gate",
    "privacy_gate",
    "authority_gate",
    "health_gate",
    "p95_gate",
    "async_queue_scored",
    "price_scored",
}

REQUIRED_DECISION_FIELDS = {
    "schema_version",
    "decision_id",
    "packet_id",
    "lane",
    "authority_level",
    "exposure_origin",
    "exposure_state",
    "validator_required",
    "validator_pass",
    "execution_mode",
    "executed",
    "budget",
    "selected_backend_id",
    "eligible_backend_ids",
    "candidates",
    "reason_code",
    "privacy",
}

REQUIRED_CANDIDATE_FIELDS = {
    "backend_id",
    "provider",
    "transport",
    "model",
    "privacy_class",
    "authority_class",
    "p95_ms",
    "estimated_cost_usd",
    "eligible",
    "stage",
    "reason_codes",
}

ALLOWED_DECISION_FIELDS = REQUIRED_DECISION_FIELDS | {"trace_id", "async_queue_candidates", "created_at"}
ALLOWED_BUDGET_FIELDS = {"mode", "p95_ms", "p90_ms", "max_cost_usd", "async_fallback"}
ALLOWED_PRIVACY_FIELDS = {"metadata_only", "raw_payload_logged", "local_output_logged"}
ALLOWED_CANDIDATE_FIELDS = REQUIRED_CANDIDATE_FIELDS | {"healthy"}


def validate_broker_decision_dict(data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a metadata-only broker decision packet.

    This intentionally mirrors the public JSON Schema without adding jsonschema as
    a runtime dependency. It is a conservative CLI/reference validator, not a
    private router implementation.
    """
    _reject_forbidden_keys(data)
    _require_exact_object_fields(data, REQUIRED_DECISION_FIELDS, ALLOWED_DECISION_FIELDS, "broker decision")

    _require_const(data, "schema_version", "0.1")
    _require_string(data, "decision_id")
    _require_string(data, "packet_id")
    _require_string(data, "lane")
    authority_level = _require_string(data, "authority_level")
    if not AUTHORITY_LEVEL_RE.match(authority_level):
        raise SovereigntyPolicyError("authority_level must match A0-A6")
    _require_enum(data, "exposure_origin", EXPOSURE_ORIGINS)
    _require_enum(data, "exposure_state", EXPOSURE_STATES)
    _require_bool(data, "validator_required")
    _require_bool(data, "validator_pass")
    _require_enum(data, "execution_mode", EXECUTION_MODES)
    if data["executed"] is not False:
        raise SovereigntyPolicyError("executed must be false for broker decisions")

    selected_backend_id = data["selected_backend_id"]
    if selected_backend_id is not None and not isinstance(selected_backend_id, str):
        raise SovereigntyPolicyError("selected_backend_id must be a string or null")

    eligible_backend_ids = _require_string_list(data, "eligible_backend_ids")
    candidates = _require_sequence(data, "candidates")
    for index, candidate in enumerate(candidates):
        _validate_candidate(candidate, f"candidates[{index}]")

    if "async_queue_candidates" in data:
        async_candidates = _require_sequence(data, "async_queue_candidates")
        for index, candidate in enumerate(async_candidates):
            _validate_candidate(candidate, f"async_queue_candidates[{index}]")

    if selected_backend_id is not None and selected_backend_id not in eligible_backend_ids:
        raise SovereigntyPolicyError("selected_backend_id must appear in eligible_backend_ids")

    _validate_budget(_require_mapping(data, "budget"))
    _require_string(data, "reason_code")
    _validate_privacy(_require_mapping(data, "privacy"))
    return dict(data)


def _validate_budget(budget: Mapping[str, Any]) -> None:
    _reject_forbidden_keys(budget)
    _require_exact_object_fields(budget, {"mode", "max_cost_usd"}, ALLOWED_BUDGET_FIELDS, "budget")
    _require_enum(budget, "mode", BUDGET_MODES)
    _require_number(budget, "max_cost_usd")
    if budget["mode"] == "sync" and "p95_ms" not in budget:
        raise SovereigntyPolicyError("p95_ms is required for sync budget mode")
    for key in ("p95_ms", "p90_ms"):
        if key in budget:
            _require_nonnegative_int(budget, key)
    if "async_fallback" in budget:
        _require_bool(budget, "async_fallback")


def _validate_privacy(privacy: Mapping[str, Any]) -> None:
    _reject_forbidden_keys(privacy)
    _require_exact_object_fields(
        privacy,
        {"metadata_only", "raw_payload_logged", "local_output_logged"},
        ALLOWED_PRIVACY_FIELDS,
        "privacy",
    )
    if privacy["metadata_only"] is not True:
        raise SovereigntyPolicyError("privacy.metadata_only must be true")
    if privacy["raw_payload_logged"] is not False:
        raise SovereigntyPolicyError("privacy.raw_payload_logged must be false")
    if privacy["local_output_logged"] is not False:
        raise SovereigntyPolicyError("privacy.local_output_logged must be false")


def _validate_candidate(candidate: Any, label: str) -> None:
    if not isinstance(candidate, Mapping):
        raise SovereigntyPolicyError(f"{label} must be an object")
    _reject_forbidden_keys(candidate)
    _require_exact_object_fields(candidate, REQUIRED_CANDIDATE_FIELDS, ALLOWED_CANDIDATE_FIELDS, label)
    _require_string(candidate, "backend_id")
    _require_string(candidate, "provider")
    _require_enum(candidate, "transport", TRANSPORTS)
    _require_string(candidate, "model")
    _require_enum(candidate, "privacy_class", PRIVACY_CLASSES)
    _require_enum(candidate, "authority_class", AUTHORITY_CLASSES)
    _require_nonnegative_int(candidate, "p95_ms")
    _require_number(candidate, "estimated_cost_usd")
    _require_bool(candidate, "eligible")
    if "healthy" in candidate:
        _require_bool(candidate, "healthy")
    stages = _require_string_list(candidate, "stage")
    unknown_stages = sorted(set(stages) - STAGES)
    if unknown_stages:
        raise SovereigntyPolicyError(f"{label}.stage has unknown values: {unknown_stages}")
    _require_string_list(candidate, "reason_codes")


def _reject_forbidden_keys(value: Any, path: str = "") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}" if path else key_text
            if FORBIDDEN_KEY_RE.search(key_text):
                raise SovereigntyPolicyError(f"forbidden broker decision key: {child_path}")
            _reject_forbidden_keys(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_keys(child, f"{path}[{index}]")


def _require_exact_object_fields(
    data: Mapping[str, Any], required: set[str], allowed: set[str], label: str
) -> None:
    missing = sorted(required - data.keys())
    if missing:
        raise SovereigntyPolicyError(f"{label} missing required fields: {missing}")
    extra = sorted(set(data.keys()) - allowed)
    if extra:
        raise SovereigntyPolicyError(f"{label} has unknown fields: {extra}")


def _require_mapping(data: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = data.get(key)
    if not isinstance(value, Mapping):
        raise SovereigntyPolicyError(f"{key} must be an object")
    return value


def _require_sequence(data: Mapping[str, Any], key: str) -> Sequence[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise SovereigntyPolicyError(f"{key} must be an array")
    return value


def _require_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise SovereigntyPolicyError(f"{key} is required")
    return value


def _require_string_list(data: Mapping[str, Any], key: str) -> list[str]:
    value = _require_sequence(data, key)
    if any(not isinstance(item, str) or not item for item in value):
        raise SovereigntyPolicyError(f"{key} must contain only non-empty strings")
    return list(value)


def _require_bool(data: Mapping[str, Any], key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise SovereigntyPolicyError(f"{key} must be a boolean")
    return value


def _require_number(data: Mapping[str, Any], key: str) -> float | int:
    value = data.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        raise SovereigntyPolicyError(f"{key} must be a non-negative number")
    return value


def _require_nonnegative_int(data: Mapping[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise SovereigntyPolicyError(f"{key} must be a non-negative integer")
    return value


def _require_enum(data: Mapping[str, Any], key: str, allowed: set[str]) -> str:
    value = _require_string(data, key)
    if value not in allowed:
        raise SovereigntyPolicyError(f"{key} has invalid value: {value}")
    return value


def _require_const(data: Mapping[str, Any], key: str, expected: str) -> None:
    if data.get(key) != expected:
        raise SovereigntyPolicyError(f"{key} must be {expected}")
