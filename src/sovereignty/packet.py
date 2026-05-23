from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .exposure import Exposure
from .policy import SovereigntyPolicyError
from .redaction import redact_model_metadata


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


def validate_packet(packet: ReviewPacket) -> ReviewPacket:
    if not packet.packet_id:
        raise SovereigntyPolicyError("packet_id is required")
    if not packet.lane:
        raise SovereigntyPolicyError("lane is required")
    if not packet.action:
        raise SovereigntyPolicyError("action is required")
    if packet.side_effects and not packet.review_required:
        raise SovereigntyPolicyError("review_required must be true when side_effects are proposed")
    packet.model_metadata = redact_model_metadata(packet.model_metadata)
    return packet
