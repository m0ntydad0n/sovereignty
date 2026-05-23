# First demo: local prep, main-agent authority

This demo describes the first Sovereignty workflow to implement and keep reproducible.

## Goal

Show a local model or local worker preparing a review packet while the main agent retains authority over the final action.

## Scenario

A user asks an agent to draft a Slack reply from a private thread.

1. The raw thread is passed to a local lane.
2. The local lane extracts facts and drafts a candidate reply.
3. The local lane returns a Sovereignty `ReviewPacket`.
4. The packet includes:
   - redacted model metadata;
   - exposure classification;
   - caller-attested or measured trust model;
   - no side effects performed by the local lane.
5. The main agent reviews the packet.
6. If a Slack send is needed, the main agent proposes or executes it under its own tool policy, not the local lane's authority.

## Packet shape

```python
from sovereignty import Exposure, ReviewPacket, validate_packet

packet = ReviewPacket(
    packet_id="pkt_demo",
    lane="writer",
    action="draft",
    local_output={
        "facts": ["The deploy is delayed", "The new ETA is tomorrow"],
        "draft": "Quick update: deploy is delayed; new ETA is tomorrow.",
    },
    model_metadata={
        "provider": "ollama",
        "model": "qwen3:8b",
        "base_url": "http://localhost:11434/v1",  # redacted by Sovereignty
    },
    exposure=Exposure(
        classification="summary",
        trust_model="caller_attested",
    ),
    side_effects=[],
    review_required=False,
)

validate_packet(packet)
```

## Success criteria

- The packet validates.
- Host-local URLs and secrets are removed from metadata.
- The local lane does not send the Slack message.
- Any proposed send action requires review by the main agent or human.

## Next iteration

Add a measured-exposure variant using a local recording proxy or verifier. Until then, caller-attested exposure must be labeled as an assertion, not proof.
