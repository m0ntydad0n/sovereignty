"""Create a minimal Sovereignty review packet.

Run from the repository root:

    python examples/basic_packet.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sovereignty import Exposure, ReviewPacket, validate_packet  # noqa: E402


packet = ReviewPacket(
    packet_id="pkt_demo_basic",
    lane="writer",
    action="draft",
    local_output={
        "facts": ["The deploy is delayed", "The new ETA is tomorrow"],
        "draft": "Quick update: deploy is delayed; new ETA is tomorrow.",
    },
    model_metadata={
        "provider": "ollama",
        "model": "qwen3:8b",
        "base_url": "http://localhost:11434/v1",
        "api_key": "sk-not-real",
    },
    exposure=Exposure(
        classification="summary",
        trust_model="caller_attested",
    ),
    side_effects=[],
    review_required=False,
)

print(validate_packet(packet).to_json())
