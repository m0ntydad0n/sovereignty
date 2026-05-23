"""Hermes adapter sketch for Sovereignty.

This example shows how a Hermes local-worker tool can return a Sovereignty
review packet instead of unstructured local output. It is intentionally not the
core library: Sovereignty's core is the packet/policy contract.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4

from sovereignty import Exposure, ReviewPacket, validate_packet

ACTION_TO_COMMAND = {
    "route": "route",
    "classify": "classify",
    "extract": "extract",
    "draft": "draft",
    "code_plan": "code-plan",
    "code_review": "code-review",
    "traceback": "traceback",
}

ACTION_TO_LANE = {
    "route": "extractor",
    "classify": "extractor",
    "extract": "extractor",
    "draft": "writer",
    "code_plan": "coder",
    "code_review": "coder",
    "traceback": "coder",
}


def run_local_worker_as_packet(
    *,
    action: str,
    text: str,
    worker_bin: str | Path,
    model_metadata: dict[str, Any],
    exposure_classification: str = "summary",
    exposure_trust_model: str = "caller_attested",
    timeout_seconds: int = 240,
) -> ReviewPacket:
    """Run a local worker action and wrap the result in a review packet.

    This adapter does not grant the local worker side-effect authority. Any
    proposed side effect must be represented in the packet and reviewed by the
    caller/main agent.
    """
    if action not in ACTION_TO_COMMAND:
        raise ValueError(f"unsupported action: {action}")
    if not text.strip():
        raise ValueError("text is required")

    proc = subprocess.run(
        [str(worker_bin), ACTION_TO_COMMAND[action], "-"],
        input=text,
        text=True,
        capture_output=True,
        timeout=timeout_seconds + 15,
        check=False,
    )
    local_output = {
        "ok": proc.returncode == 0,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "returncode": proc.returncode,
    }
    packet = ReviewPacket(
        packet_id=f"pkt_{uuid4().hex}",
        lane=ACTION_TO_LANE[action],
        action=action,
        local_output=local_output,
        model_metadata=model_metadata,
        exposure=Exposure(
            classification=exposure_classification,
            trust_model=exposure_trust_model,
        ),
        side_effects=[],
        review_required=False,
    )
    return validate_packet(packet)


def packet_to_json(packet: ReviewPacket) -> str:
    return json.dumps(packet, default=lambda value: getattr(value, "__dict__", str(value)))
