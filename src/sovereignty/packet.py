from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from .exposure import Exposure
from .policy import SovereigntyPolicyError
from .redaction import redact_model_metadata
from .side_effects import validate_side_effect_proposals


@dataclass
class ReviewPacket:
    packet_id: str
    lane: str
    action: str
    local_output: Any
    model_metadata: dict[str, Any]
    exposure: Exposure
    side_effects: list[dict[str, Any]] = field(default_factory=list)
    review_required: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        self.model_metadata = redact_model_metadata(self.model_metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "packet_id": self.packet_id,
            "lane": self.lane,
            "action": self.action,
            "local_output": self.local_output,
            "model_metadata": redact_model_metadata(self.model_metadata),
            "exposure": {
                "classification": self.exposure.classification,
                "trust_model": self.exposure.trust_model,
                "evidence": self.exposure.evidence,
            },
            "side_effects": self.side_effects,
            "review_required": self.review_required,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ReviewPacket":
        exposure_data = _required_mapping(data, "exposure")
        exposure = Exposure(
            classification=_required_string(exposure_data, "classification"),
            trust_model=_required_string(exposure_data, "trust_model"),
            evidence=exposure_data.get("evidence"),
        )
        packet = cls(
            schema_version=str(data.get("schema_version") or "0.1"),
            packet_id=_required_string(data, "packet_id"),
            lane=_required_string(data, "lane"),
            action=_required_string(data, "action"),
            local_output=data.get("local_output"),
            model_metadata=dict(_required_mapping(data, "model_metadata")),
            exposure=exposure,
            side_effects=list(data.get("side_effects") or []),
            review_required=bool(data.get("review_required")),
        )
        return validate_packet(packet)


def validate_packet(packet: ReviewPacket) -> ReviewPacket:
    if not packet.packet_id:
        raise SovereigntyPolicyError("packet_id is required")
    if not packet.lane:
        raise SovereigntyPolicyError("lane is required")
    if not packet.action:
        raise SovereigntyPolicyError("action is required")
    if packet.side_effects and not packet.review_required:
        raise SovereigntyPolicyError("review_required must be true when side_effects are proposed")
    packet.side_effects = validate_side_effect_proposals(packet.side_effects)
    packet.model_metadata = redact_model_metadata(packet.model_metadata)
    return packet


def validate_packet_dict(data: Mapping[str, Any]) -> ReviewPacket:
    return ReviewPacket.from_dict(data)


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
