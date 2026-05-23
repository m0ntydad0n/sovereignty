from __future__ import annotations

import json

from sovereignty import RecordingBoundary


LOCAL_INPUT = "Board packet says revenue is down 17%."


def fake_cloud_transport(method: str, url: str, body: bytes) -> dict[str, object]:
    # In a real adapter this is where requests/httpx/urllib would send the call.
    # The recording boundary observes the request before this transport runs.
    return {"status": 200, "received_bytes": len(body)}


def main() -> None:
    boundary = RecordingBoundary(
        local_input=LOCAL_INPUT,
        transport=fake_cloud_transport,
    )
    response = boundary.request(
        "POST",
        "https://api.example.invalid/v1/chat/completions",
        json.dumps({"prompt": f"summarize: {LOCAL_INPUT}"}).encode("utf-8"),
    )
    report = boundary.report(drop_observed_bodies=True)

    print(json.dumps({"transport_response": response, "measured_report": report}, indent=2))


if __name__ == "__main__":
    main()
